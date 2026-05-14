from flight.application.flight_service import advance_status
from flight.domain.flight import Flight
from datetime import datetime


def _do_takeoff(
    flight: Flight,
    depart_runway,
    terminals: dict,
    gates: dict,
    occupied_gates: list,
    active_flights: list,
    new_departures: dict,
    airports: dict,
):
    advance_status(flight)
    flight.time_spent = 0
    flight.departure_time = datetime.now()

    depart_airport = airports.get(flight.depart_airport_id)
    if depart_airport:
        flight.lat = depart_airport.lat
        flight.lon = depart_airport.lon
    else:
        raise ValueError(
            f"Aéroport de départ '{flight.depart_airport_id}' introuvable pour {flight.flight_code}"
        )

    new_departures.pop(flight.id, None)

    if flight in depart_runway.scheduled_flights:
        depart_runway.scheduled_flights.remove(flight)

    if flight not in active_flights:
        active_flights.append(flight)
