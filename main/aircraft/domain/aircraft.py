from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from aircraft.domain.aircraft_type import AircraftType

@dataclass
class Aircraft:
    id: str
    aircraft_code: str
    seats: int
    passengers: int
    aircraft_type: AircraftType
    maximum_speed: float
    cruising_speed: float
    operating_empty_weight_kg: float
    maximum_total_operating_weight_kg: float
    max_fuel_kg: float
    fuel_flow_cruise_kg_per_s: float
    base_rate_of_climb_ft_per_min: int
    wing_area_m2: float
    ld_ratio: float


    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    BASE_FUEL_FLOW = {
        "lineup":   0.2,   # kg/s
        "takeoff":  2.8,   # kg/s  (pleine puissance)
        "climb":    2.1,   # kg/s
        "cruise":   0.85,  # kg/s  (régime normal)
        "descent":  0.25,  # kg/s
        "landing":  0.3,   # kg/s
    }
    
    CL_max = {
    "clean":       1.4,   # croisière, ailes propres
    "takeoff":     2.0,   # flaps décollage partiellement sortis
    "landing":     2.7,   # flaps + slats complètement sortis
}

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
