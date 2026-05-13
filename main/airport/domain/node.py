from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from airport.domain.enums.node_status import NodeStatus
from airport.domain.enums.node_type import NodeType

@dataclass
class Node:
    id: str
    type: NodeType
    ref: str
    lat: float
    lon: float
    status: NodeStatus = NodeStatus.OPEN

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_open(self) -> bool:
        return self.status == NodeStatus.OPEN

    def is_gate(self) -> bool:
        return self.type == NodeType.GATE

    def is_intersection(self) -> bool:
        return self.type == NodeType.INTERSECTION

    def is_runway_threshold(self) -> bool:
        return self.type == NodeType.RUNWAY_THRESHOLD

    def is_waypoint(self) -> bool:
        return self.type == NodeType.WAYPOINT
