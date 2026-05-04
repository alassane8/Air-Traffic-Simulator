
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class NodeType(str, Enum):
    GATE = "gate"
    INTERSECTION = "intersection"
    RUNWAY_THRESHOLD = "runway_threshold"

@dataclass
class Node:
    id: str
    type: NodeType
    ref: str
    lat: float
    lon: float
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def is_gate(self) -> bool:
        return self.status == NodeType.GATE
    
    def is_intersection(self) -> bool:
        return self.status == NodeType.INTERSECTION
    
    def is_runway_threshold(self) -> bool:
        return self.status == NodeType.RUNWAY_THRESHOLD
    
    def get_node_ref(self) -> str:
        return self.ref