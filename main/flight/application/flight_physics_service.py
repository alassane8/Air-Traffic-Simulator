import math
from datetime import datetime

from flight.domain.flight import Flight


def update_position(flight: Flight, sim_tick: float) -> None:
    """
    Déplace le vol d'un tick vers sa destination.
    La vitesse est calculée pour atteindre dest_lat/dest_lon
    exactement à estimated_arrival_time.
    """
    if not flight.is_airborne:
        return

    lat1, lon1 = math.radians(flight.lat), math.radians(flight.lon)
    lat2, lon2 = math.radians(flight.dest_lat), math.radians(flight.dest_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    a = max(0.0, min(1.0, a))

    distance_km = 6371 * 2 * math.asin(math.sqrt(a))

    if distance_km < 1e-6:
        flight.lat = flight.dest_lat
        flight.lon = flight.dest_lon
        return

    now = datetime.now()
    if flight.estimated_arrival_time and flight.estimated_arrival_time > now:
        remaining_seconds = (flight.estimated_arrival_time - now).total_seconds()
        speed_km_s = distance_km / remaining_seconds
    else:
        speed_km_s = flight.speed_km_h / 3600

    dist_tick = speed_km_s * sim_tick

    if distance_km <= dist_tick:
        flight.lat = flight.dest_lat
        flight.lon = flight.dest_lon
        return

    fraction = dist_tick / distance_km
    d = 2 * math.asin(math.sqrt(a))

    if abs(math.sin(d)) < 1e-10:
        flight.lat = flight.dest_lat
        flight.lon = flight.dest_lon
        return

    A = math.sin((1 - fraction) * d) / math.sin(d)
    B = math.sin(fraction * d) / math.sin(d)

    x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
    y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
    z = A * math.sin(lat1) + B * math.sin(lat2)

    flight.lat = math.degrees(math.atan2(z, math.sqrt(x ** 2 + y ** 2)))
    flight.lon = math.degrees(math.atan2(y, x))


def has_reached_destination(flight: Flight) -> bool:
    return (
        abs(flight.lat - flight.dest_lat) < 1e-6
        and abs(flight.lon - flight.dest_lon) < 1e-6
    )


def get_distance_km(flight: Flight) -> float:
    lat1, lon1 = math.radians(flight.lat), math.radians(flight.lon)
    lat2, lon2 = math.radians(flight.dest_lat), math.radians(flight.dest_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    a = max(0.0, min(1.0, a))
    return 6371 * 2 * math.asin(math.sqrt(a))
