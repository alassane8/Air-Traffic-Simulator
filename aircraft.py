# models/airport.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AircraftType(str, Enum):
    CARGOS = "CARGOS"
    NARROW = "NARROW"
    LARGE = "LARGE"


@dataclass
class Aircraft:
    id: str
    aircraft_code: str
    seats: int
    passengers: int
    aircraft_type: AircraftType
    maximum_speed: float
    cruising_speed: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)