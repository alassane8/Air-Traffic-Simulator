from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from edge import Edge
from gate import Gate
from node import Node
from runway import Runway
from terminal import Terminal

@dataclass
class TaxiwayGraph:
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

@dataclass
class Airport:
    id: str
    airport_code: str
    lat: float
    lon: float

    terminals: List[Terminal] = field(default_factory=list)
    gates: List[Gate] = field(default_factory=list)
    runways: List[Runway] = field(default_factory=list)

    taxiway_graph: List[TaxiwayGraph] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    gates_by_id: Dict[str, Gate] = field(init=False, default_factory=dict)
    terminals_by_id: Dict[str, Terminal] = field(init=False, default_factory=dict)
    runways_by_id: Dict[str, Runway] = field(init=False, default_factory=dict)

    def get_free_gates(self) -> List[Gate]:
        return [g for g in self.gates if g.status == "FREE"]

    def get_free_runways(self) -> List[Runway]:
        return [r for r in self.runways if r.status == "FREE"]

    def get_terminal_gates(self, terminal_id: str) -> List[Gate]:
        return [g for g in self.gates if g.terminal_id == terminal_id]

    def resolve_node_ref(self, node: "Node"):
        if node.type == "gate":
            return self.gates_by_id.get(node.ref)
        elif node.type == "runway_threshold":
            return self.runways_by_id.get(node.ref)
        return None