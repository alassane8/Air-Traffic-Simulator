from enum import Enum


class RunwayStatus(str, Enum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"
    CLOSED = "CLOSED"
    MAINTENANCE = "MAINTENANCE"
