from enum import Enum

class RunwayUsageType(Enum):
    DEPARTURE = "DEPARTURE"
    ARRIVAL = "ARRIVAL"

    def __init__(self, label: str):
        self.label = label

