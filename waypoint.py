


from dataclasses import dataclass, field
from datetime import datetime

class WaypointStatus:
    OPEN =  "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Waypoint:
    id: str
    name: str
    lat: float
    lon: float
    min_alt_ft: int
    max_alt_ft: int

    status: WaypointStatus

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


    def is_open(self) -> bool:
        return self.status == WaypointStatus.OPEN