from flight.application.flight_service import advance_status
from flight.domain.flight import Flight
from datetime import datetime


def _do_takeoff(
    flight: Flight,
    depart_runway,
    active_flights: list,
    new_departures: dict,
    airports: dict,
    air_corridors: dict,
):
    advance_status(flight)
    flight.time_spent = 0
    flight.departure_time = datetime.now()

    depart_airport = airports.get(flight.depart_airport_id)
    if depart_airport:
        flight.lat = depart_airport.lat
        flight.lon = depart_airport.lon
        flight.altitude_m = 0.0
    else:
        raise ValueError(
            f"Aéroport de départ '{flight.depart_airport_id}' introuvable pour {flight.flight_code}"
        )
    flight.current_waypoint_index = 0
    if air_corridors:
        corridor = next(
            (c for c in air_corridors.values() if c.air_corridor_code == flight.corridor_code),
            None,
        )
        if corridor and corridor.waypoints:
            wp = corridor.waypoints[0]
            flight.dest_lat = wp.lat
            flight.dest_lon = wp.lon
            flight.altitude_m = (wp.min_alt_ft + wp.max_alt_ft) / 2 * 0.3048

    new_departures.pop(flight.id, None)

    if flight in depart_runway.scheduled_flights:
        depart_runway.scheduled_flights.remove(flight)

    if flight not in active_flights:
        active_flights.append(flight)