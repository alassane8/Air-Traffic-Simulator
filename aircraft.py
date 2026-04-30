# models/airport.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Aircraft:
    id: str
    aircraft_code: str
    seats: int
    passengers: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)