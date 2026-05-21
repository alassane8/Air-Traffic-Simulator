import datetime
import random
from typing import Optional
import uuid
from xml.dom import Node

from airport.domain.enums.node_status import NodeStatus
from incident.domain.enums.incident_status import IncidentStatus
from incident.domain.inicident import Incident
from incident.application import zone_manager
from incident.domain.bounding_box import BoundingBox
from waypoint.domain.waypoint import Waypoint
from waypoint.domain.waypoint_status import WaypointStatus


def create_node_incident(nodes: dict[str, Node], expires_at: datetime = None) -> Incident:
        candidate = random.choice([n for n in nodes.values() 
                    if not n.is_runway_threshold() and not n.is_closed()])
        candidate.status = NodeStatus.CLOSED

        return Incident(id = str(uuid.uuid4()),
                        incident_code = Incident._build_incident_code(candidate, None),
                        cause = Incident._pick_node_cause(),
                        status = IncidentStatus.ACTIVE,
                        node = candidate,
                        expires_at = expires_at,
                        )

def create_waypoint_incident(waypoints: dict[str, Waypoint], expires_at: datetime = None) -> Incident:
        candidate = random.choice([w for w in waypoints.values()
                    if not w.is_closed() and not w.is_near_airport()])
        candidate.status = WaypointStatus.CLOSED

        return Incident(id = str(uuid.uuid4()),
                        incident_code = Incident._build_incident_code(None, candidate),
                        cause = Incident._pick_waypoint_cause(),
                        status = IncidentStatus.ACTIVE,
                        waypoint = candidate,
                        expires_at = expires_at,
        )

def create_waypoints_zone_incident(waypoints: dict[str, Waypoint], bbox: Optional[BoundingBox] = None, expires_at: datetime = None) -> Incident:
        zone_id = f"INC-{str(uuid.uuid4())[:8].upper()}"
        cause   = Incident._pick_waypoint_cause()

        if bbox:
            zone = zone_manager._apply_closure(
                zone_id    = zone_id,
                label      = zone_id,
                reason     = cause.label,
                bbox       = bbox,
                expires_at = expires_at,
            )
        else:
            raise ValueError("bbox ou (center_lat, center_lon, radius_km) requis")

        affected_waypoints = {
            wp_id: waypoints[wp_id]
            for wp_id in zone.affected_waypoint_ids
            if wp_id in waypoints
        }

        anchor = next(iter(affected_waypoints.values()), None)

        return Incident(id = str(uuid.uuid4()),
                        incident_code = Incident._build_incident_code(None, anchor, is_zone=True),
                        cause = cause,
                        status  = IncidentStatus.ACTIVE,
                        waypoints = affected_waypoints,
                        zone_id = zone_id,
                        expires_at = expires_at,
        )

def resolve_incident(incident: Incident) -> None:
        if incident.node:
            incident.node.status = NodeStatus.OPEN

        if incident.nodes:
            for n in incident.nodes.values():
                n.status = NodeStatus.OPEN

        if incident.waypoint:
            incident.waypoint.status = WaypointStatus.OPEN

        if incident.waypoints and incident.zone_id:
            zone_manager.reopen_zone(incident.zone_id)

        incident.resolve()