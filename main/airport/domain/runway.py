from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime

from main.airport.domain.enums.runway_status import RunwayStatus

@dataclass
class Runway:
    id: str
    airport_id: str
    length: float
    heading: int
    status: RunwayStatus
    current_aircraft: Optional[str] = None
    scheduled_flights: List = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_available(self) -> bool:
        return self.status == RunwayStatus.FREE and self.current_aircraft is None

    def is_occupied(self) -> bool:
        return self.status == RunwayStatus.OCCUPIED

    def is_operational(self) -> bool:
        return self.status in {RunwayStatus.FREE, RunwayStatus.OCCUPIED}

    def assign_aircraft(self, aircraft_id: str) -> bool:
        if not self.is_available():
            return False
        self.current_aircraft = aircraft_id
        self.status = RunwayStatus.OCCUPIED
        self.updated_at = datetime.now()
        return True

    def release_aircraft(self) -> None:
        self.current_aircraft = None
        if self.status != RunwayStatus.CLOSED:
            self.status = RunwayStatus.FREE
        self.updated_at = datetime.now()

    def can_schedule(self) -> bool:
        return self.status not in {RunwayStatus.CLOSED, RunwayStatus.MAINTENANCE}

    def add_flight(self, flight) -> bool:
        if not self.can_schedule():
            return False
        self.scheduled_flights.append(flight)
        self.updated_at = datetime.now()
        return True

    def remove_flight(self, flight_id: str) -> bool:
        for f in self.scheduled_flights:
            if getattr(f, "id", None) == flight_id:
                self.scheduled_flights.remove(f)
                self.updated_at = datetime.now()
                return True
        return False

    def next_flight(self):
        if not self.scheduled_flights:
            return None
        return sorted(
            self.scheduled_flights,
            key=lambda f: getattr(f, "scheduled_time", datetime.max),
        )[0]

    def set_status(self, status: RunwayStatus) -> None:
        self.status = status
        if status != RunwayStatus.OCCUPIED:
            self.current_aircraft = None
        self.updated_at = datetime.now()
