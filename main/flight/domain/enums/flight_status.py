from enum import Enum

class FlightStatus(Enum):
    PLANNED    = ("PLANNED", 0)
    LINEUP     = ("LINEUP", 10)
    TAKEOFF    = ("TAKEOFF", 6)
    CLIMBING   = ("CLIMBING", 6)
    CRUISE     = ("CRUISE", None)
    DESCENDING = ("DESCENDING", 6)
    LANDING    = ("LANDING", 6)
    TAXI       = ("TAXI", 10)
    PARKED     = ("PARKED", None)

    def __init__(self, label: str, duration_seconds: int | None):
        self.label = label
        self.duration_seconds = duration_seconds

