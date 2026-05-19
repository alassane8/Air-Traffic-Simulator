from enum import Enum


class IncidentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    
    def __init__(self, label: str):
        self.label = label
