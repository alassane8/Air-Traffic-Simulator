from enum import Enum


class CorridorStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    RESTRICTED = "RESTRICTED"

