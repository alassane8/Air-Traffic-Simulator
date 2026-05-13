from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from main.waypoint.domain.waypoint_status import WaypointStatus

@dataclass
class Waypoint:
    id: str
    lat: float
    lon: float
    min_alt_ft: int
    max_alt_ft: int
    status: WaypointStatus

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_open(self) -> bool:
        return self.status == WaypointStatus.OPEN

    def is_closed(self) -> bool:
        return self.status == WaypointStatus.CLOSED
