
from flight.application.flight_service import advance_status
from flight.domain.flight import Flight


def _do_start_descent(flight: Flight, air_corridors: dict, aircrafts: dict):
    for corridor in air_corridors.values():
        if corridor.air_corridor_code == flight.corridor_code:
            aircraft = aircrafts.get(flight.aircraft_code)
            if aircraft and aircraft in corridor.aircrafts:
                corridor.aircrafts.remove(aircraft)
            break

    advance_status(flight)
    flight.time_spent = 0

def _do_land(flight: Flight, runways: dict, active_flights: list):
    for runway in runways.values():
        if runway.id == flight.arrival_runway_code:
            if flight in runway.scheduled_flights:
                runway.scheduled_flights.remove(flight)
            break

    advance_status(flight)
    flight.time_spent = 0

