from dataclasses import dataclass, field
import datetime
from typing import Optional
from incident.domain.bounding_box import BoundingBox
from main.incident.domain.enums.waypoint_incident_cause import WaypointIncidentCause

@dataclass
class ClosureZone:
    zone_id: str
    label: str
    reason: WaypointIncidentCause
    bbox: Optional[BoundingBox]
    affected_waypoint_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None