from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Flight:
    id: str
    flight_code: str
    flight_status: str # "PLANIFIÉ" | "EMBARQUEMENT" | "ROULAGE" | "DÉCOLLAGE" | "CROISIÈRE" | "APPROCHE" | "ATTERRISSAGE"
    aircraft_code: str
    priority: str  # "URGENCE" | "CARBURANT_CRITIQUE" | "MÉDICAL" | "RETARD" | "NORMAL"
    estimated_departure_time: datetime = field(default_factory=datetime.now)
    estimated_arrival_time: datetime = field(default_factory=datetime.now)
    departure_time: datetime = field(default_factory=datetime.now)
    arrival_time: datetime = field(default_factory=datetime.now)
    depart_airport_code: str
    depart_terminal_code:str
    depart_gate_code: str
    depart_runway_code: str
    corridor_code: str
    arrival_airport_code: str
    arrival_terminal_code:str
    arrival_gate_code: str
    arrival_runway_code: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
