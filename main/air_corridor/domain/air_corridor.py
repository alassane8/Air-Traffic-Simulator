from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List

from main.air_corridor.domain.air_corridor_direction import CorridorDirection
from main.air_corridor.domain.air_corridor_status import CorridorStatus

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
    aircrafts: List = field(default_factory=list)
    waypoints: List = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_open(self) -> bool:
        return self.status == CorridorStatus.OPEN

    def is_full(self) -> bool:
        return len(self.aircrafts) >= self.max_capacity

    def has_capacity(self) -> bool:
        return len(self.aircrafts) < self.max_capacity

    def can_accept_aircraft(self) -> bool:
        return self.is_open() and self.has_capacity()

    def add_aircraft(self, aircraft) -> bool:
        if not self.can_accept_aircraft():
            return False
        self.aircrafts.append(aircraft)
        self.updated_at = datetime.now()
        return True

    def remove_aircraft(self, aircraft_id: str) -> bool:
        for a in self.aircrafts:
            if getattr(a, "id", None) == aircraft_id:
                self.aircrafts.remove(a)
                self.updated_at = datetime.now()
                return True
        return False

    def contains_aircraft(self, aircraft_id: str) -> bool:
        return any(getattr(a, "id", None) == aircraft_id for a in self.aircrafts)

    def available_slots(self) -> int:
        return max(0, self.max_capacity - len(self.aircrafts))

    def set_status(self, status: CorridorStatus) -> None:
        self.status = status
        self.updated_at = datetime.now()

    def is_direction_allowed(self, from_airport: str, to_airport: str) -> bool:
        if self.direction == CorridorDirection.BIDIRECTIONAL:
            return True
        return self.from_airport == from_airport and self.to_airport == to_airport
