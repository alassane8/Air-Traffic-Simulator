from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
from aircraft import Aircraft

class CorridorStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    RESTRICTED = "RESTRICTED"


class CorridorDirection(str, Enum):
    UNIDIRECTIONAL = "UNIDIRECTIONAL"
    BIDIRECTIONAL = "BIDIRECTIONAL"

@dataclass
class AirCorridor:
    id: str
    air_corridor_code: str
    from_airport: str
    to_airport: str
    distance: float
    altitude: str
    direction: CorridorDirection
    status: CorridorStatus
    max_capacity: int
    aircrafts: List[Aircraft] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
