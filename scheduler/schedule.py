from datetime import datetime
import time
from typing import List

from a_star_algorithm import find_path_graph
from air_corridor import AirCorridor
from aircraft import Aircraft
from airline import Airline
from airport import Airport
from edge import Edge
from flight import Flight, FlightStatus, RunwayUsageType
from flight_helpers import advanceStatus, getEstimatedDuration, isDeparting
from gate import Gate
import init_logs
from node import Node
from runway import Runway
from scheduler import flight_physics, runway_manager
from scheduler.flight_timing import initFlightCruisingTime, initFlightEstimatedArrivalTime
from terminal import Terminal
from waypoint import Waypoint


def simulation(
    terminals: dict, waypoints: dict, aircrafts: dict, airports: dict,
    airCorridors: dict, airlines: dict, runways: dict, occupied_gates: list,
    edges: dict, nodes: dict, gates: dict
):
    TICK_INTERVAL = 1.0
    active_flights = []

    # Initialisation : 50 DEPARTURE dans leurs runways, aucune runway d'arrivée encore
    new_departures = runway_manager.assign_flight_to_departure_runway(
        terminals, aircrafts, airlines, runways, occupied_gates, airports, airCorridors
    )

    while True:
        tick_start = time.time()

        init_logs.log_runways(runways)

        # ── Boucle DÉPART ────────────────────────────────────────────────────
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
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.LINEUP.duration_seconds:
                    advanceStatus(flight)   # → TAKEOFF
                    flight.time_spent = 0

            elif flight.status == FlightStatus.TAKEOFF:
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.TAKEOFF.duration_seconds:
                    _takeoff(flight, depart_runway, gates, occupied_gates, active_flights, new_departures, airports)
                    
                    aircraft = aircrafts.get(flight.aircraft_code)
                    air_corridor = next(
                        (c for c in airCorridors.values() if c.air_corridor_code == flight.corridor_code),
                        None
                    )
                    
                    if aircraft and air_corridor:
                        cruising_time = initFlightCruisingTime(aircraft, air_corridor)
                        flight.estimated_arrival_time = initFlightEstimatedArrivalTime(flight, cruising_time)
                    else:
                        print(f"[WARN] {flight.flight_code} : aircraft={aircraft} corridor={air_corridor}")

        # ── Boucle EN VOL ────────────────────────────────────────────────────
        for flight in list(active_flights):

            if flight.status == FlightStatus.CLIMBING:
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.CLIMBING.duration_seconds:
                    advanceStatus(flight)
                    flight.time_spent = 0
                    aircraft = aircrafts.get(flight.aircraft_code)
                    if aircraft:
                        flight.speed_knots = aircraft.cruising_speed

            elif flight.status == FlightStatus.CRUISE:
                flight.time_spent += TICK_INTERVAL

                runway_manager.assign_arrival_runway(flight, airports)
                flight_physics.update_position(flight, TICK_INTERVAL)

                if flight_physics.has_reached_destination(flight):
                    _start_descent(flight, airCorridors, aircrafts)

            elif flight.status == FlightStatus.DESCENDING:
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.DESCENDING.duration_seconds:
                    advanceStatus(flight)
                    flight.time_spent = 0

            elif flight.status == FlightStatus.LANDING:
                flight.time_spent += TICK_INTERVAL
                if flight.time_spent >= FlightStatus.LANDING.duration_seconds:
                    _land(flight, runways, active_flights)

        elapsed = time.time() - tick_start
        time.sleep(max(0, TICK_INTERVAL - elapsed))


# ── FONCTIONS INTERNES ────────────────────────────────────────────────────────

def _takeoff(flight: Flight, depart_runway: object, gates: dict, occupied_gates: list, active_flights: list, new_departures: dict, airports: dict):
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

    # Retirer de la runway de départ
    if flight in depart_runway.scheduled_flights:
        depart_runway.scheduled_flights.remove(flight)

    # Libérer la gate
    gate = gates.get(flight.depart_gate_code)
    if gate and gate in occupied_gates:
        occupied_gates.remove(gate)

    # Retirer de la file d'attente de départ
    new_departures.pop(flight.id, None)

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

    # Retirer de la runway d'arrivée scheduled_flights — il sera remis en LANDING
    advanceStatus(flight)   # → DESCENDING
    flight.time_spent = 0


def _land(flight: Flight, runways: dict, active_flights: list):
    """Le vol atterrit : retirer de la runway d'arrivée et de active_flights."""
    # Retirer de la runway d'arrivée
    for runway in runways.values():
        if runway.id == flight.arrival_runway_code:
            if flight in runway.scheduled_flights:
                runway.scheduled_flights.remove(flight)
            break

    advanceStatus(flight)   # → PARKED
    flight.arrival_time = datetime.now()

    if flight in active_flights:
        active_flights.remove(flight)


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