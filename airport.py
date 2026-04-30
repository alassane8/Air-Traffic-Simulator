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