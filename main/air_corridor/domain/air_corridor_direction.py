from enum import Enum


class CorridorDirection(str, Enum):
    UNIDIRECTIONAL = "UNIDIRECTIONAL"
    BIDIRECTIONAL = "BIDIRECTIONAL"