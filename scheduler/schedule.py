from datetime import datetime, timedelta
import time
from typing import List
from xml.dom import Node

from a_star_algorithm import find_path_graph, path_total_distance
from air_corridor import AirCorridor
from aircraft import Aircraft
from airline import Airline
from airport import Airport, get_terminal
from edge import Edge
from flight import Flight, FlightStatus
from flight_helpers import advanceStatus, isDeparting
from gate import Gate, GateStatus
import init_logs
from runway import Runway
from scheduler import flight_physics, runway_manager
from scheduler.flight_timing import initFlightCruisingTime, initFlightEstimatedArrivalTime
from terminal import Terminal


def simulation(
    terminals: dict, waypoints: dict, aircrafts: dict, airports: dict,
    airCorridors: dict, airlines: dict, runways: dict, occupied_gates: list,
    edges: dict, nodes: dict, gates: dict
):
    TIME_SCALE = 60
    TICK_INTERVAL = 1.0
    SIM_TICK = TICK_INTERVAL * TIME_SCALE
    active_flights = []

    new_departures = runway_manager.assign_flight_to_departure_runway(
        terminals, aircrafts, airlines, runways, occupied_gates, airports, airCorridors, existing_departures={}
    )

    while True:
        tick_start = time.time()

        init_logs.log_runways(runways)

        runway_simulation(new_departures, occupied_gates, active_flights, terminals, nodes, edges, runways, gates, airports, aircrafts, airCorridors, TIME_SCALE, TICK_INTERVAL)

        flight_simulation(active_flights, TICK_INTERVAL, TIME_SCALE, SIM_TICK, airCorridors, airports, aircrafts, runways)

        landing_simulation(active_flights, occupied_gates, new_departures, aircrafts, airlines, airCorridors, terminals, runways, airports, nodes, edges, gates, TICK_INTERVAL)

        elapsed = time.time() - tick_start
        time.sleep(max(0, TICK_INTERVAL - elapsed))

def _takeoff(flight: Flight, depart_runway: object, terminals: dict, gates: dict, occupied_gates: list, active_flights: list, new_departures: dict, airports: dict):
    """Le vol décolle : quitte la runway de départ, entre dans active_flights."""
    advanceStatus(flight)   # → CLIMBING
    flight.time_spent = 0

    flight.departure_time = datetime.now()  # heure réelle, pas estimée

    # Positionner le vol aux coordonnées réelles de l'aéroport de départ
    depart_airport = airports.get(flight.depart_airport_code)
    if depart_airport:
        flight.lat = depart_airport.lat
        flight.lon = depart_airport.lon
    else:
        raise ValueError(f"Aéroport de départ '{flight.depart_airport_code}' introuvable pour {flight.flight_code}")

    new_departures.pop(flight.id, None)

    # Retirer de la runway de départ
    if flight in depart_runway.scheduled_flights:
        depart_runway.scheduled_flights.remove(flight)

    if flight not in active_flights:
        active_flights.append(flight)


def _start_descent(flight: Flight, airCorridors: dict, aircrafts: dict):
    """Le vol a atteint la destination : retirer du corridor, passer en DESCENDING."""
    for corridor in airCorridors.values():
        if corridor.air_corridor_code == flight.corridor_code:
            aircraft = aircrafts.get(flight.aircraft_code)
            if aircraft and aircraft in corridor.aircrafts:
                corridor.aircrafts.remove(aircraft)
            break

    advanceStatus(flight)   # → DESCENDING
    flight.time_spent = 0


def _land(flight: Flight, runways: dict, active_flights: list):
    """Le vol atterrit : retirer de la runway d'arrivée et de active_flights."""
    for runway in runways.values():
        if runway.id == flight.arrival_runway_code:
            if flight in runway.scheduled_flights:
                runway.scheduled_flights.remove(flight)
            break

    advanceStatus(flight)
    flight.time_spent = 0

# ── UTILITAIRES ───────────────────────────────────────────────────────────────

def get_path_to_runway(flight: Flight, nodes: dict, edges: dict) -> List[str]:
    start_id = goal_id = None

    for node in nodes.values():
        if node.ref == flight.depart_gate_code:
            start_id = node.id
        elif node.ref == flight.depart_runway_code:
            goal_id = node.id

    if not start_id or not goal_id:
        raise ValueError(f"Gate '{flight.depart_gate_code}' ou runway '{flight.depart_runway_code}' introuvable")

    return find_path_graph(nodes, edges, start_id, goal_id)

def runway_simulation(new_departures: dict, occupied_gates: list, active_flights: list,
                      terminals: dict, nodes: dict, edges: dict, runways: dict, gates: dict,
                      airports: dict, aircrafts: dict, airCorridors: dict,
                      TIME_SCALE: float, TICK_INTERVAL: float):

        for flight in list(new_departures.values()):
            get_path_to_runway(flight, nodes, edges)

            depart_runway = runways.get(flight.depart_runway_code)
            if not depart_runway:
                continue

            # Seuls les vols DEPARTURE de cet aéroport sont ordonnés
            departure_queue = [
                f for f in depart_runway.scheduled_flights
                if isDeparting(f) and f.depart_airport_code == depart_runway.airport_id
            ]

            if not departure_queue or departure_queue[0] != flight:
                continue

            if flight.status == FlightStatus.PLANNED:
                advanceStatus(flight)   # → LINEUP
                flight.time_spent = 0

            elif flight.status == FlightStatus.LINEUP:
                # Libérer la gate une seule fois, au premier tick de LINEUP
                if flight.time_spent == 0:
                    gate = gates.get(flight.depart_gate_code)
                    if gate and gate in occupied_gates:
                        occupied_gates.remove(gate)
                        gate.release_aircraft()
                    terminal = next(
                        (t for t in terminals.values()
                        if t.terminal_code == flight.depart_terminal_code
                        and t.airport_id == flight.depart_airport_code),
                        None
                    )
                    if terminal:
                        terminal.remove_plane()

                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.LINEUP.duration_seconds:
                    advanceStatus(flight)   # → TAKEOFF
                    flight.time_spent = 0

            elif flight.status == FlightStatus.TAKEOFF:
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.TAKEOFF.duration_seconds:
                    _takeoff(flight, depart_runway, terminals, gates, occupied_gates, active_flights, new_departures, airports)

                    aircraft = aircrafts.get(flight.aircraft_code)
                    air_corridor = next(
                        (c for c in airCorridors.values() if c.air_corridor_code == flight.corridor_code),
                        None
                    )

                    if aircraft and air_corridor:
                        cruising_time = initFlightCruisingTime(aircraft, air_corridor, TIME_SCALE)
                        flight.estimated_arrival_time = initFlightEstimatedArrivalTime(flight, cruising_time)
                    else:
                        print(f"[WARN] {flight.flight_code} : aircraft={aircraft} corridor={air_corridor}")

def flight_simulation(active_flights: list,
                      TICK_INTERVAL: float, TIME_SCALE: float, SIM_TICK: float,
                      airCorridors: dict, airports: dict, aircrafts: dict, runways: dict):

        for flight in list(active_flights):

            if flight.status == FlightStatus.CLIMBING:
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.CLIMBING.duration_seconds:
                    advanceStatus(flight)
                    flight.time_spent = 0
                    aircraft = aircrafts.get(flight.aircraft_code)
                    if aircraft:
                        flight.speed_km_h = aircraft.cruising_speed
                runway_manager.assign_arrival_runway(flight, airports)

            elif flight.status == FlightStatus.CRUISE:
                flight.time_spent += SIM_TICK

                flight_physics.update_position(flight, SIM_TICK)

                if not flight_physics.has_reached_destination(flight):
                    distance_restante = flight_physics.get_distance_km(flight)
                    speed_km_s = flight.speed_km_h / 3600
                    seconds_left = (distance_restante / speed_km_s) / TIME_SCALE
                    flight.estimated_arrival_time = datetime.now() + timedelta(seconds=seconds_left)

                if flight_physics.has_reached_destination(flight):
                    _start_descent(flight, airCorridors, aircrafts)

            elif flight.status == FlightStatus.DESCENDING:
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.DESCENDING.duration_seconds:
                    advanceStatus(flight)
                    flight.time_spent = 0


def landing_simulation(active_flights: list, occupied_gates: list, new_departures: dict,
                       aircrafts: dict, airlines: dict, airCorridors: dict, terminals: dict,
                       runways: dict, airports: dict, nodes: dict, edges: dict, gates: dict,
                       TICK_INTERVAL: float):

    for flight in list(active_flights):
        arrival_airport = airports.get(flight.arrival_airport_code)

        if flight.status == FlightStatus.LANDING:
            flight.time_spent += TICK_INTERVAL

            if flight.time_spent >= FlightStatus.LANDING.duration_seconds:

                # ── FIX : guard si arrival_runway_code est None ──
                if not flight.arrival_runway_code:
                    print(f"[WARN] {flight.flight_code} en LANDING sans runway d'arrivée, on réessaie l'assignation")
                    assigned = runway_manager.assign_arrival_runway(flight, airports)
                    if not assigned:
                        # Toujours pas de runway : on bloque et on attend
                        flight.time_spent = FlightStatus.LANDING.duration_seconds
                        continue

                best_distance = float("inf")
                available_gates = {}
                best_gate = find_best_landing_gate(
                    best_distance, arrival_airport, available_gates,
                    runways, nodes, edges, terminals, flight
                )

                if best_gate is None:
                    # ── FIX : compteur anti-deadlock ──
                    flight._gate_wait_ticks = getattr(flight, '_gate_wait_ticks', 0) + 1
                    if flight._gate_wait_ticks % 30 == 0:
                        print(f"[WARN] {flight.flight_code} bloqué en attente de gate "
                              f"depuis {flight._gate_wait_ticks} ticks")
                    flight.time_spent = FlightStatus.LANDING.duration_seconds
                    continue

                # Réinitialiser le compteur d'attente si on a trouvé une gate
                flight._gate_wait_ticks = 0

                # Stocker la gate sur le vol pour la retrouver au tick TAXI
                flight._landing_gate = best_gate

                _land(flight, runways, active_flights)   # retire de active_flights et passe ARRIVED
                flight.arrival_gate_code = best_gate.id
                flight.arrival_terminal_code = best_gate.terminal

        elif flight.status == FlightStatus.TAXI:
            flight.time_spent += TICK_INTERVAL

            if flight.time_spent >= FlightStatus.TAXI.duration_seconds:
                gate = gates.get(flight.arrival_gate_code)
                
                if gate:
                    gate.assign_aircraft(flight.aircraft_code)
                    if gate not in occupied_gates:  
                        occupied_gates.append(gate)

                    arrival_terminal = terminals.get(gate.terminal)
                    if arrival_terminal:
                        arrival_terminal.add_plane()

                advanceStatus(flight)

                if flight in active_flights:
                    active_flights.remove(flight)

                freshly_assigned = runway_manager.assign_flight_to_departure_runway(
                    terminals, aircrafts, airlines, runways, occupied_gates, airports, airCorridors,
                    existing_departures=new_departures
                )
                new_departures.update(freshly_assigned)

def find_best_landing_gate(best_distance: float, arrival_airport, available_gates: dict,
                           runways: dict, nodes: dict, edges: dict, terminals: dict,
                           flight: Flight) -> Gate:

    if arrival_airport is None:
        return None

    for gate in arrival_airport.gates:
        if gate.is_free():
            available_gates[gate.id] = gate

    ref_to_node_id = {node.ref: node.id for node in nodes.values()}

    # ── FIX : guard si arrival_runway_code est None ──
    if not flight.arrival_runway_code:
        return None

    runway = runways.get(flight.arrival_runway_code)
    if not runway:
        print(f"[WARN] Runway d'arrivée '{flight.arrival_runway_code}' introuvable pour {flight.flight_code}")
        return None

    start_id = ref_to_node_id.get(runway.id)
    if not start_id:
        return None

    best_gate = None

    for gate in available_gates.values():
        terminal = terminals.get(gate.terminal)
        if terminal is None:
            continue
        if not terminal.can_accept_plane() or not terminal.is_open():
            continue

        goal_id = ref_to_node_id.get(gate.id)
        if not goal_id:
            continue

        path = find_path_graph(nodes, edges, start_id, goal_id)
        if not path:
            continue

        distance = path_total_distance(path, nodes, edges)
        if distance < best_distance:
            best_distance = distance
            best_gate = gate

    return best_gate