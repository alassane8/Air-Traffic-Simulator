from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from flight.domain.enums.flight_priority import FlightPriority
from flight.domain.enums.flight_status import FlightStatus
from flight.domain.enums.runway_usage_type import RunwayUsageType


@dataclass
class Flight:
    id: str
    flight_code: str
    flight_status: FlightStatus
    airline_id: str
    aircraft_id: str
    priority: FlightPriority
    depart_airport_id: str
    depart_terminal_code: str
    depart_gate_code: str
    depart_runway_code: str
    corridor_code: str
    arrival_airport_code: str
    arrival_terminal_code: str
    arrival_gate_code: str
    arrival_runway_code: str
    runway_usage: RunwayUsageType = RunwayUsageType.DEPARTURE

    estimated_departure_time: datetime = field(default_factory=datetime.now)
    estimated_arrival_time: datetime = field(default_factory=datetime.now)
    departure_time: datetime = field(default_factory=datetime.now)
    arrival_time: datetime = field(default_factory=datetime.now)

    lat: float = 0.0
    lon: float = 0.0
    altitude_m: float = 0.0
    heading: float = 0.0
    speed_km_h: float = 0.0

    dest_lat: float = 0.0
    dest_lon: float = 0.0

    fuel_kg: float = 0.0
    fuel_burn_rate_kg_per_s: float = 0.0

    time_spent: float = 0.0

    current_waypoint_index: int = 0
    reverse_corridor: bool = False
    CL_max: float = 1.4

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def status(self) -> 'FlightStatus':
        return self.flight_status

    @status.setter
    def status(self, value: 'FlightStatus'):
        self.flight_status = value

    @property
    def is_airborne(self) -> bool:
        return self.flight_status in (
            FlightStatus.CLIMBING,
            FlightStatus.CRUISE,
            FlightStatus.DESCENDING,
        )

    @property
    def is_fuel_critical(self) -> bool:
        if self.fuel_burn_rate_kg_per_s <= 0:
            return False
        remaining_seconds = self.fuel_kg / self.fuel_burn_rate_kg_per_s
        return remaining_seconds < 1800  # 30 min