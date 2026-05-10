from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Edge:
    id: str
    from_node_id: str
    to_node_id: str
    taxiway: str
    distance_m: float

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def connects(self, node_id: str) -> bool:
        return self.from_node_id == node_id or self.to_node_id == node_id

    def is_between(self, node_a: str, node_b: str) -> bool:
        return (
            (self.from_node_id == node_a and self.to_node_id == node_b)
            or (self.from_node_id == node_b and self.to_node_id == node_a)
        )

    def get_other_node(self, node_id: str) -> str | None:
        if node_id == self.from_node_id:
            return self.to_node_id
        if node_id == self.to_node_id:
            return self.from_node_id
        return None

    def is_loop(self) -> bool:
        return self.from_node_id == self.to_node_id

    def length_km(self) -> float:
        return self.distance_m / 1000
