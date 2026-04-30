# models/airport.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Aircraft:
    id: str
    aircraft_code: str
    seats: int
    passengers: int
    aircraft_type: str  #"CARGOS" | "NARROW" | "LARGE"
    maximum_speed: float
    crusing_speed: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)