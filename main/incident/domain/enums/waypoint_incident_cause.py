from enum import Enum


class WaypointIncidentCause(Enum):
    SEVERE_WEATHER = ("SEVERE_WEATHER", .28)
    CLEAR_AIR_TURBULENCE = ("CLEAR_AIR_TURBULENCE", .22)
    MILITARY_EXERCISE = ("MILITARY_EXERCISE", .18)
    ATC_CAPACITY = ("ATC_CAPACITY", .10)
    VOLCANIC_ASH = ("VOLCANIC_ASH", .04)
    THUNDERSTORM = ("THUNDERSTORM", .08)
    NAVIGATION_AID_FAILURE = ("NAVIGATION_AID_FAILURE", .05)
    ROCKET_LAUNCH = ("ROCKET_LAUNCH", .02)
    SEARCH_AND_RESCUE = ("SEARCH_AND_RESCUE", .01)
    VIP_MOVEMENT = ("VIP_MOVEMENT", .02)

    def __init__(self, label: str, weight: float):
        self.label = label
        self.weight = weight