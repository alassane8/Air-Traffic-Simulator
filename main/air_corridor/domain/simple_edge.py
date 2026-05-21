from dataclasses import dataclass

@dataclass
class SimpleEdge:
    from_node_id: str
    to_node_id: str
    distance_m: float