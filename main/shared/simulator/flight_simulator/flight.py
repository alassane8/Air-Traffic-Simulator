from datetime import datetime, timedelta

from airport.application.runway_assignment_service import assign_arrival_runway
from flight.application.flight_physics_service import (
    get_distance_km,
    has_reached_destination,
    update_position,
    update_flight_fuel,
)
from flight.application.flight_service import advance_status
from flight.domain.flight import FlightStatus
from shared.simulator.landing_simulator.descent import _do_start_descent


def _tick_flight(
    active_flights: list,
    tick_interval: float,
    time_scale: float,
    sim_tick: float,
    air_corridors: dict,
    airports: dict,
    aircrafts: dict,
    runways: dict,
):
    for flight in list(active_flights):

        # ── Consommation carburant – toutes phases en vol ──────────
        # tick_interval est en secondes réelles ; update_flight_fuel
        # applique le bon facteur selon flight.status.
        update_flight_fuel(flight, tick_interval)

        if flight.status == FlightStatus.CLIMBING:
            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.CLIMBING.duration_seconds:
                advance_status(flight)
                flight.time_spent = 0
                aircraft = aircrafts.get(flight.aircraft_id)
                if aircraft:
                    flight.speed_km_h = aircraft.cruising_speed
            assign_arrival_runway(flight, airports)

        elif flight.status == FlightStatus.CRUISE:
            flight.time_spent += sim_tick
            update_position(flight, sim_tick)

            if not has_reached_destination(flight):
                distance_restante = get_distance_km(flight)
                speed_km_s = flight.speed_km_h / 3600
                seconds_left = (distance_restante / speed_km_s) / time_scale
                flight.estimated_arrival_time = datetime.now() + timedelta(seconds=seconds_left)

            if has_reached_destination(flight):
                _do_start_descent(flight, air_corridors, aircrafts)

        elif flight.status == FlightStatus.DESCENDING:
            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.DESCENDING.duration_seconds:
                advance_status(flight)
                flight.time_spent = 0