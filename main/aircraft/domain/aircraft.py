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

    def is_full(self) -> bool:
        return self.passengers >= self.seats

    def has_capacity(self) -> bool:
        return self.passengers < self.seats

    def available_seats(self) -> int:
        return max(0, self.seats - self.passengers)

    def load_passengers(self, count: int) -> bool:
        if self.passengers + count > self.seats:
            return False
        self.passengers += count
        self.updated_at = datetime.now()
        return True

    def unload_passengers(self, count: int) -> bool:
        if self.passengers - count < 0:
            return False
        self.passengers -= count
        self.updated_at = datetime.now()
        return True

    def is_cargo(self) -> bool:
        return self.aircraft_type == AircraftType.CARGOS

    def is_passenger(self) -> bool:
        return self.aircraft_type in {AircraftType.NARROW, AircraftType.LARGE}

    def set_cruising_speed(self, speed: float) -> None:
        if speed <= self.maximum_speed:
            self.cruising_speed = speed
            self.updated_at = datetime.now()

    def is_overspeed(self) -> bool:
        return self.cruising_speed > self.maximum_speed
