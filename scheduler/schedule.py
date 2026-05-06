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
from flight_helpers import advanceStatus, getEstimatedDuration
from gate import Gate
import init_logs
from node import Node
from runway import Runway
from scheduler import flight_physics, runway_manager
import simulator
from terminal import Terminal
from waypoint import Waypoint

def simulation(terminals: dict[Terminal], waypoints: dict[Waypoint], aircrafts: dict[Aircraft], airports: dict[Airport], airCorridors: dict[AirCorridor], airlines: dict[Airline], runways: dict[Runway], occupied_gates: list[Gate], edges: dict[Edge], nodes: dict[Node], gates: dict[Gate]):
    TICK_INTERVAL = 1.0
    active_flights = []

    new_departures = runway_manager.assign_flight_to_departure_runway(terminals, aircrafts, airlines, runways, occupied_gates, edges, nodes)
    runway_manager.assign_flight_to_arrival_runway(runways, airports, aircrafts, airCorridors)

    while True:
        tick_start = time.time()
            
        init_logs.log_runways(runways)

        for flight in new_departures.values():
            get_path_to_runway(flight, nodes, edges)
                
            for runway in runways.values():
                if flight not in runway.scheduled_flights:
                    continue

                scheduled_flights = runway.scheduled_flights

                if not scheduled_flights or scheduled_flights[0] != flight:
                    continue

                if flight.status == FlightStatus.PLANNED:
                    advanceStatus(flight)  # → LINEUP
                    flight.time_spent = 0

                elif flight.status == FlightStatus.LINEUP:
                    flight.time_spent += TICK_INTERVAL
                    lineup_duration = FlightStatus.LINEUP.duration_seconds

                    if flight.time_spent >= lineup_duration:
                        advanceStatus(flight)
                        flight.time_spent = 0

                elif flight.status == FlightStatus.TAKEOFF:
                    flight.time_spent += TICK_INTERVAL
                    takeoff_duration = FlightStatus.TAKEOFF.duration_seconds

                    if flight.time_spent >= takeoff_duration:
                        takeoff(flight, scheduled_flights)
                        occupied_gates.remove(gates[flight.depart_gate_code])
        
            flight.lat = get_departure_airport_lat(flight, airports)
            flight.lon = get_departure_airport_lon(flight, airports)

            if flight not in active_flights:
                active_flights.append(flight)
                advanceStatus(flight)
                climbing_duration = FlightStatus.CLIMBING.duration_seconds

                if flight.time_spent >= climbing_duration:
                    advanceStatus(flight)

                    for aircraft in aircrafts.values():
                        if aircraft.id == flight.aircraft_code:
                            flight.speed_knots = aircraft.cruising_speed

        # mise a jour position lat/lon a chaque tick
        for flight in active_flights:
            flight_physics.update_position(flight, airCorridors, waypoints, TICK_INTERVAL)

                # # gestion des conflits | separation meteo croisements ralentissement detours avec A*
                # conflicts = conflict_manager.detect_all(active_flights)
                # for conflict in conflicts:
                #     conflict_manager.resolve(conflict)  # reroute, ralentit, etc.
                
        # atterrissage 
        landed = [f for f in active_flights if flight_physics.has_reached_destination(f)]

        for flight in landed:
            # Retirer de la runway d'arrivée
            for runway in runways.values():
                match = next((f for f in runway.scheduled_flights if f.id == flight.id and f.runway_usage == RunwayUsageType.ARRIVAL), None)
                if match:
                    runway.scheduled_flights.remove(match)
                    break

            # Retirer du corridor
            for corridor in airCorridors.values():
                if corridor.air_corridor_code == flight.corridor_code:
                    aircraft = aircrafts.get(flight.aircraft_code)
                    if aircraft in corridor.aircrafts:
                        corridor.aircrafts.remove(aircraft)
                    break

            advanceStatus(flight)
            active_flights.remove(flight)
        
        # nouveau vol 
        occupied_gates = simulator.assign_aircrafts_to_gates(aircrafts, gates, terminals)

        elapsed = time.time() - tick_start
        time.sleep(max(0, TICK_INTERVAL - elapsed))
        
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
        
def takeoff(flight: Flight, scheduled_flights: list[Flight]):
    advanceStatus(flight)

    flight.departure_time = datetime.now()
    flight.estimated_departure_time = datetime.now()

    flight.estimated_arrival_time = flight.estimated_departure_time + getEstimatedDuration(flight)

    scheduled_flights.remove(flight)


def get_departure_airport_lat(flight, airports):
    for airport in airports.values():
        if airport.id == flight.depart_airport_code:
            return airport.lat
    return None

def get_departure_airport_lon(flight, airports):
    for airport in airports.values():
        if airport.id == flight.depart_airport_code:
            return airport.lon
    return None