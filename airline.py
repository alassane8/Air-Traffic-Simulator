# models/airport.py
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Airline:
    id: str
    name: str
    iata_code: str
    icao_code: str
    country: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)