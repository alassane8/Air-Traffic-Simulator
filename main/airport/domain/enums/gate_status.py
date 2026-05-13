from enum import Enum


class GateStatus(str, Enum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
