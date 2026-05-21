from dataclasses import dataclass, field
import datetime
import random
from typing import Optional
from xml.dom import Node

from airport.domain.enums.node_status import NodeStatus
from incident.domain.enums.incident_status import IncidentStatus
from incident.domain.enums.node_incident_cause import NodeIncidentCause
from incident.domain.enums.waypoint_incident_cause import WaypointIncidentCause
from waypoint.domain.waypoint import Waypoint


@dataclass
class Incident: 
    id: str
    incident_code: str
    cause: NodeIncidentCause | WaypointIncidentCause
    status: IncidentStatus

    node: Optional[Node] = None
    nodes: Optional[dict[str, Node]] = None
    waypoint: Optional[Waypoint] = None
    waypoints: Optional[dict[str, Waypoint]] = None

    zone_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None


    @property
    def is_node_incident(self) -> bool:
        return self.node is not None or self.nodes is not None

    @property
    def is_waypoint_incident(self) -> bool:
        return self.waypoint is not None or self.waypoints is not None

    @property
    def is_zone_incident(self) -> bool:
        """Incident multi-éléments (zone manager impliqué)."""
        return (self.nodes is not None and len(self.nodes) > 1) or \
               (self.waypoints is not None and len(self.waypoints) > 1)

    def resolve(self) -> None:
        self.status     = IncidentStatus.RESOLVED
        self.updated_at = datetime.now()

    
    def pick_waypoint_incident_cause() -> WaypointIncidentCause:
            causes  = list(WaypointIncidentCause)
            weights = [c.weight for c in causes]
            return random.choices(causes, weights=weights, k=1)[0]

    def pick_node_incident_cause() -> NodeIncidentCause:
            causes  = list(NodeIncidentCause)
            weights = [c.weight for c in causes]
            return random.choices(causes, weights=weights, k=1)[0]


    @staticmethod
    def _build_incident_code(
        node:     Optional[Node],
        waypoint: Optional[Waypoint],
        is_zone:  bool = False,
    ) -> str:
        code_number = random.randrange(10, 99)

        if is_zone:
            prefix    = node.id if node else (waypoint.id if waypoint else "ZN")
            code_type = "ZNT" if node else "ZWP"   # Zone-Node / Zone-Waypoint
        elif node is not None:
            prefix    = node.id
            code_type = "INT" if node.is_intersection() else "NOD"
        elif waypoint is not None:
            prefix    = waypoint.id
            code_type = "WPT"
        else:
            raise ValueError("node ou waypoint requis pour générer un code incident")

        return f"{prefix}-{code_type}-{code_number}"