import time
from typing import List

from a_star_algorithm import find_path_graph
from air_corridor import AirCorridor
from aircraft import Aircraft
from airline import Airline
from airport import Airport
from edge import Edge
from flight import Flight
from gate import Gate
import init_logs
from node import Node
from runway import Runway
from scheduler import runway_manager
import simulator
from terminal import Terminal

def simulation(terminals: dict[Terminal], aircrafts: dict[Aircraft], airports: dict[Airport], airCorridors: dict[AirCorridor], airlines: dict[Airline], runways: dict[Runway], occupied_gates: list[Gate], edges: dict[Edge], nodes: dict[Node], gates: dict[Gate]):
    TICK_INTERVAL = 1.0
    active_flights = []
        
    while True:
        tick_start = time.time()
    
        new_departures = runway_manager.assign_flight_to_departure_runway(terminals, aircrafts, airlines, runways, occupied_gates, edges, nodes)

        runway_manager.assign_flight_to_arrival_runway(runways, airports, aircrafts, airCorridors)
            
        init_logs.log_runways(runways)

        # phase de decollage taxi Algoritm A* -> piste de decollage -> init lat/lon de l'avion 
        for flight in new_departures.values():
            print(get_path_to_runway(flight, nodes, edges))
        #       enlever l'avion de la runway une fois decoller
        #     takeoff(flight)
            occupied_gates.remove(gates[flight.depart_gate_code])
            
        #     flight.lat = get_departure_airport_lat(depart_airport_code)
        #     flight.lon = get_departure_airport_lon(depart_airport_code)

        #     active_flights.append(flight)

        # # mise a jour position lat/lon a chaque tick
        # for flight in active_flights:
        #     flight_physics.update_position(flight, TICK_INTERVAL)

        # # gestion des conflits | separation meteo croisements ralentissement detours avec A*
        # conflicts = conflict_manager.detect_all(active_flights)
        # for conflict in conflicts:
        #     conflict_manager.resolve(conflict)  # reroute, ralentit, etc.
        
        # # atterrissage 
        # landed = [f for f in active_flights if flight_physics.has_reached_destination(f)]
        # for flight in landed:
        #     flight.land()
        #     active_flights.remove(flight)
        
        # # nouveau vol 
        # occupied_gates = simulator.assign_aircrafts_to_gates(aircrafts, gates, terminals)

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