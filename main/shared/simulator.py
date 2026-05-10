from datetime import datetime, timedelta
import time
from typing import List

from airport.application.taxiway_pathfinding_service import find_path_graph
from airport.application.runway_assignment_service import (
    assign_flight_to_departure_runway,
    assign_arrival_runway,
)
from airport.application.gate_assignment_service import find_best_landing_gate
from flight.domain.flight import Flight, FlightStatus
from flight.application.flight_service import advance_status, is_departing
from flight.application.flight_timing_service import (
    init_flight_cruising_time,
    init_flight_estimated_arrival_time,
)
from flight.application.flight_physics_service import (
    update_position,
    has_reached_destination,
    get_distance_km,
)
from airport.application.runway_assignment_service import assign_arrival_runway
from shared import init_logger


def run_simulation(
    terminals: dict,
    waypoints: dict,
    aircrafts: dict,
    airports: dict,
    air_corridors: dict,
    airlines: dict,
    runways: dict,
    occupied_gates: list,
    edges: dict,
    nodes: dict,
    gates: dict,
):
    TIME_SCALE = 60
    TICK_INTERVAL = 1.0
    SIM_TICK = TICK_INTERVAL * TIME_SCALE
    active_flights = []

    new_departures = assign_flight_to_departure_runway(
        terminals, aircrafts, airlines, runways, occupied_gates,
        airports, air_corridors, existing_departures={}
    )

    while True:
        tick_start = time.time()

        init_logger.log_runways(runways)

        _tick_runway(
            new_departures, occupied_gates, active_flights,
            terminals, nodes, edges, runways, gates,
            airports, aircrafts, air_corridors, TIME_SCALE, TICK_INTERVAL,
        )

        _tick_flight(
            active_flights, TICK_INTERVAL, TIME_SCALE, SIM_TICK,
            air_corridors, airports, aircrafts, runways,
        )

        _tick_landing(
            active_flights, occupied_gates, new_departures,
            aircrafts, airlines, air_corridors, terminals,
            runways, airports, nodes, edges, gates, TICK_INTERVAL,
        )

        elapsed = time.time() - tick_start
        time.sleep(max(0, TICK_INTERVAL - elapsed))


# ── RUNWAY TICK ───────────────────────────────────────────────────────────────

def _get_path_to_runway(flight: Flight, nodes: dict, edges: dict) -> List[str]:
    start_id = goal_id = None

    for node in nodes.values():
        if node.ref == flight.depart_gate_code:
            start_id = node.id
        elif node.ref == flight.depart_runway_code:
            goal_id = node.id

    if not start_id or not goal_id:
        raise ValueError(
            f"Gate '{flight.depart_gate_code}' ou runway '{flight.depart_runway_code}' introuvable"
        )

    return find_path_graph(nodes, edges, start_id, goal_id)


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
    advance_status(flight)  # → CLIMBING
    flight.time_spent = 0
    flight.departure_time = datetime.now()

    depart_airport = airports.get(flight.depart_airport_code)
    if depart_airport:
        flight.lat = depart_airport.lat
        flight.lon = depart_airport.lon
    else:
        raise ValueError(
            f"Aéroport de départ '{flight.depart_airport_code}' introuvable pour {flight.flight_code}"
        )

    new_departures.pop(flight.id, None)

    if flight in depart_runway.scheduled_flights:
        depart_runway.scheduled_flights.remove(flight)

    if flight not in active_flights:
        active_flights.append(flight)


def _do_start_descent(flight: Flight, air_corridors: dict, aircrafts: dict):
    for corridor in air_corridors.values():
        if corridor.air_corridor_code == flight.corridor_code:
            aircraft = aircrafts.get(flight.aircraft_code)
            if aircraft and aircraft in corridor.aircrafts:
                corridor.aircrafts.remove(aircraft)
            break

    advance_status(flight)  # → DESCENDING
    flight.time_spent = 0


def _do_land(flight: Flight, runways: dict, active_flights: list):
    for runway in runways.values():
        if runway.id == flight.arrival_runway_code:
            if flight in runway.scheduled_flights:
                runway.scheduled_flights.remove(flight)
            break

    advance_status(flight)
    flight.time_spent = 0


def _tick_runway(
    new_departures: dict,
    occupied_gates: list,
    active_flights: list,
    terminals: dict,
    nodes: dict,
    edges: dict,
    runways: dict,
    gates: dict,
    airports: dict,
    aircrafts: dict,
    air_corridors: dict,
    time_scale: float,
    tick_interval: float,
):
    for flight in list(new_departures.values()):
        _get_path_to_runway(flight, nodes, edges)

        depart_runway = runways.get(flight.depart_runway_code)
        if not depart_runway:
            continue

        departure_queue = [
            f for f in depart_runway.scheduled_flights
            if is_departing(f) and f.depart_airport_code == depart_runway.airport_id
        ]

        if not departure_queue or departure_queue[0] != flight:
            continue

        if flight.status == FlightStatus.PLANNED:
            advance_status(flight)  # → LINEUP
            flight.time_spent = 0

        elif flight.status == FlightStatus.LINEUP:
            if flight.time_spent == 0:
                gate = gates.get(flight.depart_gate_code)
                if gate and gate in occupied_gates:
                    occupied_gates.remove(gate)
                    gate.release_aircraft()
                terminal = next(
                    (
                        t for t in terminals.values()
                        if t.terminal_code == flight.depart_terminal_code
                        and t.airport_id == flight.depart_airport_code
                    ),
                    None,
                )
                if terminal:
                    terminal.remove_plane()

            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.LINEUP.duration_seconds:
                advance_status(flight)  # → TAKEOFF
                flight.time_spent = 0

        elif flight.status == FlightStatus.TAKEOFF:
            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.TAKEOFF.duration_seconds:
                _do_takeoff(
                    flight, depart_runway, terminals, gates,
                    occupied_gates, active_flights, new_departures, airports,
                )

                aircraft = aircrafts.get(flight.aircraft_code)
                air_corridor = next(
                    (c for c in air_corridors.values() if c.air_corridor_code == flight.corridor_code),
                    None,
                )

                if aircraft and air_corridor:
                    cruising_time = init_flight_cruising_time(aircraft, air_corridor, time_scale)
                    flight.estimated_arrival_time = init_flight_estimated_arrival_time(
                        flight, cruising_time
                    )
                else:
                    print(f"[WARN] {flight.flight_code} : aircraft={aircraft} corridor={air_corridor}")


# ── FLIGHT TICK ───────────────────────────────────────────────────────────────

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

        if flight.status == FlightStatus.CLIMBING:
            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.CLIMBING.duration_seconds:
                advance_status(flight)
                flight.time_spent = 0
                aircraft = aircrafts.get(flight.aircraft_code)
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


# ── LANDING TICK ──────────────────────────────────────────────────────────────

def _tick_landing(
    active_flights: list,
    occupied_gates: list,
    new_departures: dict,
    aircrafts: dict,
    airlines: dict,
    air_corridors: dict,
    terminals: dict,
    runways: dict,
    airports: dict,
    nodes: dict,
    edges: dict,
    gates: dict,
    tick_interval: float,
):
    for flight in list(active_flights):
        arrival_airport = airports.get(flight.arrival_airport_code)

        if flight.status == FlightStatus.LANDING:
            flight.time_spent += tick_interval

            if flight.time_spent >= FlightStatus.LANDING.duration_seconds:
                if not flight.arrival_runway_code:
                    print(f"[WARN] {flight.flight_code} en LANDING sans runway d'arrivée, réassignation")
                    assigned = assign_arrival_runway(flight, airports)
                    if not assigned:
                        flight.time_spent = FlightStatus.LANDING.duration_seconds
                        continue

                best_gate = find_best_landing_gate(
                    arrival_airport, runways, nodes, edges, terminals, flight
                )

                if best_gate is None:
                    flight._gate_wait_ticks = getattr(flight, "_gate_wait_ticks", 0) + 1
                    if flight._gate_wait_ticks % 30 == 0:
                        print(
                            f"[WARN] {flight.flight_code} bloqué en attente de gate "
                            f"depuis {flight._gate_wait_ticks} ticks"
                        )
                    flight.time_spent = FlightStatus.LANDING.duration_seconds
                    continue

                flight._gate_wait_ticks = 0
                flight._landing_gate = best_gate

                _do_land(flight, runways, active_flights)
                flight.arrival_gate_code = best_gate.id
                flight.arrival_terminal_code = best_gate.terminal

        elif flight.status == FlightStatus.TAXI:
            flight.time_spent += tick_interval

            if flight.time_spent >= FlightStatus.TAXI.duration_seconds:
                gate = gates.get(flight.arrival_gate_code)

                if gate:
                    gate.assign_aircraft(flight.aircraft_code)
                    if gate not in occupied_gates:
                        occupied_gates.append(gate)
                    arrival_terminal = terminals.get(gate.terminal)
                    if arrival_terminal:
                        arrival_terminal.add_plane()

                advance_status(flight)

                if flight in active_flights:
                    active_flights.remove(flight)

                freshly_assigned = assign_flight_to_departure_runway(
                    terminals, aircrafts, airlines, runways,
                    occupied_gates, airports, air_corridors,
                    existing_departures=new_departures,
                )
                new_departures.update(freshly_assigned)
