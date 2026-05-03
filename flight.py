from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class RunwayUsageType(Enum):
    DEPARTURE = "DEPARTURE"
    ARRIVAL = "ARRIVAL"
    

    def __init__(self, label: str):
        self.label = label

class FlightStatus(Enum):
    PLANNED   = ("PLANNED", 0)
    BOARDING  = ("BOARDING", 120)
    LINEUP  = ("LINEUP", 60)
    TAKEOFF   = ("TAKEOFF", 6)
    CLIMBING   = ("CLIMBING", 6)
    CRUISE    = ("CRUISE", None)
    DESCENDING  = ("DESCENDING", 60)
    LANDING   = ("LANDING", 9)
    PARKED   = ("PARKED", 9)

    def __init__(self, label: str, duration_seconds: int | None):
        self.label = label
        self.duration_seconds = duration_seconds


class FlightPriority(Enum):
    EMERGENCY = ("EMERGENCY", 1)
    FUEL_CRITICAL = ("FUEL_CRITICAL", 2)
    MEDICAL = ("MEDICAL", 3)
    DELAY = ("DELAY", 4)
    NORMAL = ("NORMAL", 5)

    def __init__(self, label: str, order: int):
        self.label = label
        self.order = order


@dataclass
class Flight:
    id: str
    flight_code: str 
    flight_status: FlightStatus
    airline_id: str
    aircraft_code: str
    priority: FlightPriority
    depart_airport_code: str
    depart_terminal_code:str
    depart_gate_code: str
    depart_runway_code: str
    corridor_code: str
    arrival_airport_code: str
    arrival_terminal_code:str
    arrival_gate_code: str
    arrival_runway_code: str
    runway_usage: RunwayUsageType = RunwayUsageType.DEPARTURE
    estimated_departure_time: datetime = field(default_factory=datetime.now)
    estimated_arrival_time: datetime = field(default_factory=datetime.now)
    departure_time: datetime = field(default_factory=datetime.now)
    arrival_time: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
