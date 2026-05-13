from enum import Enum


class NodeType(str, Enum):
    GATE = "gate"
    INTERSECTION = "intersection"
    RUNWAY_THRESHOLD = "runway_threshold"
    WAYPOINT = "waypoint"