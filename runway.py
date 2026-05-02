# models/runway.py
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime
from flight import Flight


class RunwayStatus(str, Enum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"
    CLOSED = "CLOSED"
    MAINTENANCE = "MAINTENANCE"

@dataclass
class Runway:
    id: str
    airport_id: str
    length: float
    heading: int
    status: RunwayStatus  # "FREE" | "OCCUPIED" | "CLOSED" | "MAINTENANCE"
    current_aircraft: Optional[str] = None
    scheduled_flights: List[Flight] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)