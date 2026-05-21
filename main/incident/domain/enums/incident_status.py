from enum import Enum


class IncidentStatus(str, Enum):
    ACTIVE   = "ACTIVE"
    RESOLVED = "RESOLVED"
    EXPIRED  = "EXPIRED"

    
    def __init__(self, label: str):
        self.label = label
