from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from airport.domain.edge import Edge
from airport.domain.gate import Gate
from airport.domain.node import Node
from airport.domain.runway import Runway
from airport.domain.terminal import Terminal


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

    # ── Gates ─────────────────────────────────────────────────────────────────

    def get_free_gates(self) -> List[Gate]:
        return [g for g in self.gates if g.status == "FREE"]

    def get_gate(self, gate_id: str) -> Optional[Gate]:
        return self.gates_by_id.get(gate_id)

    def get_gates_by_terminal(self, terminal_id: str) -> List[Gate]:
        return [g for g in self.gates if g.terminal_id == terminal_id]

    def get_gates_by_status(self, status: str) -> List[Gate]:
        return [g for g in self.gates if g.status == status]

    # ── Terminals ─────────────────────────────────────────────────────────────

    def get_terminal(self, terminal_id: str) -> Optional[Terminal]:
        return self.terminals_by_id.get(terminal_id)

    def get_terminal_of_gate(self, gate_id: str) -> Optional[Terminal]:
        gate = self.get_gate(gate_id)
        if gate is None:
            return None
        return self.terminals_by_id.get(gate.terminal_id)

    # ── Runways ───────────────────────────────────────────────────────────────

    def get_free_runways(self) -> List[Runway]:
        return [r for r in self.runways if r.status == "FREE"]

    def get_runway(self, runway_id: str) -> Optional[Runway]:
        return self.runways_by_id.get(runway_id)

    def get_runways_by_status(self, status: str) -> List[Runway]:
        return [r for r in self.runways if r.status == status]

    # ── Taxiway graph ─────────────────────────────────────────────────────────

    def resolve_node_ref(self, node: Node):
        if node.type == "gate":
            return self.gates_by_id.get(node.ref)
        elif node.type == "runway_threshold":
            return self.runways_by_id.get(node.ref)
        return None

    def get_node(self, node_id: str) -> Optional[Node]:
        for graph in self.taxiway_graph:
            for node in graph.nodes:
                if node.id == node_id:
                    return node
        return None

    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        return [
            node
            for graph in self.taxiway_graph
            for node in graph.nodes
            if node.type == node_type
        ]

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        for graph in self.taxiway_graph:
            for edge in graph.edges:
                if edge.id == edge_id:
                    return edge
        return None

    def get_edges_of_node(self, node_id: str) -> List[Edge]:
        return [
            edge
            for graph in self.taxiway_graph
            for edge in graph.edges
            if edge.from_node_id == node_id or edge.to_node_id == node_id
        ]
