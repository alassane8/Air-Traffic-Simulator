import datetime
from typing import Optional

from incident.domain.bounding_box import BoundingBox
from incident.domain.closure_zone import ClosureZone
from waypoint.domain.waypoint import Waypoint
from waypoint.domain.waypoint_status import WaypointStatus

def _apply_closure(
        zone_id: str,
        label: str,
        reason: str,
        waypoints: list[Waypoint],
        status: WaypointStatus,
        expires_at: datetime,
        bbox: Optional[BoundingBox] = None,
    ) -> ClosureZone:
        now = datetime.now()
        for wp in waypoints:
            wp.status = status
            wp.updated_at = now

        zone = ClosureZone(
            zone_id=zone_id,
            label=label,
            reason=reason,
            bbox=bbox,
            affected_waypoint_ids=[wp.id for wp in waypoints],
            expires_at=expires_at,
        )
        _active_zones[zone_id] = zone
        return zone

def reopen_zone(zone_id: str) -> int:
        """Réouvre tous les waypoints fermés par une zone."""
        zone = _active_zones.pop(zone_id, None)
        if not zone:
            return 0
        now = datetime.now()
        count = 0
        for wp_id in zone.affected_waypoint_ids:
            wp = index._by_id.get(wp_id)
            if wp:
                wp.status = WaypointStatus.OPEN
                wp.updated_at = now
                count += 1
        return count

def expire_zones() -> list[str]:
        """Réouvre automatiquement les zones expirées."""
        now = datetime.now()
        expired = [zid for zid, z in _active_zones.items() if z.expires_at and z.expires_at <= now]
        for zid in expired:
            reopen_zone(zid)
        return expired