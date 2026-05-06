from air_corridor import AirCorridor
from aircraft import Aircraft
from flight import Flight
from scheduler.flight_timing import initFlightCruisingTime


import math

from waypoint import Waypoint
def update_position(flight: Flight, airCorridors: dict[AirCorridor], waypoints: dict[Waypoint], TICK_INTERVAL):
    if not flight.is_airborne:
        return

    lat1, lon1 = math.radians(flight.lat), math.radians(flight.lon)
    lat2, lon2 = math.radians(flight.dest_lat), math.radians(flight.dest_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    distance_km = 6371 * 2 * math.asin(math.sqrt(a))

    speed_km_s = (flight.speed_knots * 1.852) / 3600

    dist_tick = speed_km_s * TICK_INTERVAL

    if distance_km <= dist_tick:
        flight.lat = flight.dest_lat
        flight.lon = flight.dest_lon
        return

    fraction = dist_tick / distance_km

    d = 2 * math.asin(math.sqrt(a))
    A = math.sin((1 - fraction) * d) / math.sin(d)
    B = math.sin(fraction * d) / math.sin(d)

    x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
    y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
    z = A * math.sin(lat1)                  + B * math.sin(lat2)

    flight.lat = math.degrees(math.atan2(z, math.sqrt(x**2 + y**2)))
    flight.lon = math.degrees(math.atan2(y, x))

def has_reached_destination(flight: Flight) -> bool:
    return (
        abs(flight.lat - flight.dest_lat) < 1e-6 and
        abs(flight.lon - flight.dest_lon) < 1e-6
    )