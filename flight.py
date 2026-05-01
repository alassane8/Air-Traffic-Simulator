from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FlightStatus(str, Enum):
    PLANNED = "PLANNED"
    BOARDING = "BOARDING"
    ROLLING = "ROLLING"
    TAKEOFF = "TAKEOFF"
    CRUISE = "CRUISE"
    APPROCH = "APPROCH"
    LANDING = "LANDING"


class FlightPriority(str, Enum):
    EMERGENCY = "EMERGENCY"
    FUEL_CRITICAL = "FUEL_CRITICAL"
    MEDICAL = "MEDICAL"
    DELAY = "DELAY"
    NORMAL = "NORMAL"


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
    estimated_departure_time: datetime = field(default_factory=datetime.now)
    estimated_arrival_time: datetime = field(default_factory=datetime.now)
    departure_time: datetime = field(default_factory=datetime.now)
    arrival_time: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
