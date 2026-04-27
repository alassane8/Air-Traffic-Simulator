# models/airport.py
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from terminal import Terminal
from gate import Gate
from runway import Runway


@dataclass
class Airport:
    id: str
    airport_code: str
    lat: float
    long: float
    terminals: List[Terminal] = field(default_factory=list)
    gates: List[Gate] = field(default_factory=list)
    runways: List[Runway] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_gates(self) -> List[Gate]:
        return self.gates

    def get_terminals(self) -> List[Terminal]:
        return self.terminals

    def get_runways(self) -> List[Runway]:
        return self.runways

    def get_available_runways(self) -> List[Runway]:
        return [r for r in self.runways if r.is_available()]

    def get_available_gates(self) -> List[Gate]:
        return [g for g in self.gates if g.is_available()]