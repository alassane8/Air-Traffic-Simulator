from enum import Enum

class FlightPriority(Enum):
    EMERGENCY     = ("EMERGENCY", 1)
    FUEL_CRITICAL = ("FUEL_CRITICAL", 2)
    MEDICAL       = ("MEDICAL", 3)
    DELAY         = ("DELAY", 4)
    NORMAL        = ("NORMAL", 5)

    def __init__(self, label: str, order: int):
        self.label = label
        self.order = order
