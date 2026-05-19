from dataclasses import dataclass, field
import datetime
import random
from typing import Dict
import uuid
from xml.dom import Node

from main.airport.domain.enums.node_status import NodeStatus
from main.incident.domain.incident_status import IncidentStatus
from main.incident.domain.node_incident_cause import NodeIncidentCause
from main.incident.domain.waypoint_incident_cause import WaypointIncidentCause
from main.waypoint.domain.waypoint import Waypoint
from main.waypoint.domain.waypoint_status import WaypointStatus


@dataclass
class Incident: 
    id: str
    incident_code: str
    node_incident_cause: NodeIncidentCause
    waypoint_incident_cause: WaypointIncidentCause
    status: IncidentStatus
    nodes: Dict[Node]
    node: Node
    waypoints: Dict[Waypoint]
    waypoint: Waypoint
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    
def intersection_incidient_code(node: Node, waypoint: Waypoint) -> str:
        if node and node.is_intersection():
            code_number = random.randrange(10,99)
            code_type = "INT"
        elif waypoint: 
            code_number = random.randrange(10,99)
            code_type = "WPT"
        
        return node.id + code_type + code_number
    
def pick_waypoint_incident_cause() -> WaypointIncidentCause:
        causes  = list(WaypointIncidentCause)
        weights = [c.weight for c in causes]
        return random.choices(causes, weights=weights, k=1)[0]

def pick_node_incident_cause() -> NodeIncidentCause:
        causes  = list(NodeIncidentCause)
        weights = [c.weight for c in causes]
        return random.choices(causes, weights=weights, k=1)[0]

def create_node_incident(nodes: dict[Node]) -> Incident:
        randomly_choosed_node = random.choice([
            node for node in nodes.values()
            if not node.is_runway_threshold() and node.is_gate() and not node.is_closed()])

        randomly_choosed_node.status == NodeStatus.CLOSED

        return Incident(id=uuid.uuid4(),
                        incident_code=intersection_incidient_code(randomly_choosed_node, None),
                        node_incident_cause=pick_node_incident_cause(),
                        waypoint_incident_cause=pick_waypoint_incident_cause(),
                        status= IncidentStatus.ACTIVE,
                        nodes=None,
                        node=randomly_choosed_node,
                        waypoints=None,
                        waypoint=None,
                        created_at=datetime.now(),
                        updated_at=datetime.now())

    
    # def create_nodes_incident(nodes: dict[Node]):
        

def create_waypoint_incident(waypoints: Waypoint)-> Incident:
        randomly_choosed_waypoint = random.choice([
            waypoint for waypoint in waypoints.values()
            if not waypoint.is_closed() and not waypoint.is_near_airport()])

        randomly_choosed_waypoint.status == WaypointStatus.CLOSED

        return Incident(id=uuid.uuid4(),
                        incident_code=intersection_incidient_code(None, randomly_choosed_waypoint),
                        node_incident_cause=pick_node_incident_cause(),
                        waypoint_incident_cause=pick_waypoint_incident_cause(),
                        nodes=None,
                        node=None,
                        waypoints=None,
                        waypoint=randomly_choosed_waypoint,
                        created_at=datetime.now(),
                        updated_at=datetime.now())