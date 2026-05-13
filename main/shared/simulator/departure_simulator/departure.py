
from typing import List

import math

from airport.application.taxiway_pathfinding_service import find_path_graph
from flight.application.flight_service import advance_status, is_departing
from flight.application.flight_timing_service import init_flight_cruising_time, init_flight_estimated_arrival_time
from flight.domain.flight import Flight, FlightStatus
from main.air_corridor.domain.air_corridor import AirCorridor
from main.aircraft.domain.aircraft import Aircraft
from shared.simulator.departure_simulator.takeoff import _do_takeoff
from aircraft.domain.aircraft_type import AircraftType



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
            advance_status(flight)
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
                advance_status(flight)
                flight.time_spent = 0

        elif flight.status == FlightStatus.TAKEOFF:
            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.TAKEOFF.duration_seconds:
                _do_takeoff(
                    flight, depart_runway, terminals, gates,
                    occupied_gates, active_flights, new_departures, airports,
                )

                aircraft = aircrafts.get(flight.aircraft_id)
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

# def compute_flight_fuel(aircraft: Aircraft, flight: Flight, airCorridors: dict[AirCorridor]):
#     reserve_ratio = .15
#     TSFC = 0.000018
#     avg_passenger_weight_kg = 95
#     passenger_weight_kg = aircraft.passengers * avg_passenger_weight_kg
#     air_corridor = airCorridors.get(flight.corridor_code)

#     if aircraft.type == AircraftType.CARGOS:
#         payload_kg = 100000
#     if aircraft.is_passsenger():
#         payload_kg = passenger_weight_kg
    
#     flight_time_h = flight.estimated_arrival_time - flight.estimated_departure_time

#     total_fuel_kg = 5000

#     total_operating_weight_kg = aircraft.operating_empty_weight_kg + total_fuel_kg + payload_kg

#     fuel_kg = total_operating_weight_kg * (1 - math.exp(- (air_corridor.distance * TSFC) / (aircraft.ld_ratio * aircraft.cruising_speed)))

#     load_factor = total_operating_weight_kg / aircraft.maximum_total_operating_weight_kg

#     BASE_FUEL_FLOW = {
#     "taxi":     0.2,   # kg/s
#     "takeoff":  2.8,   # kg/s  (pleine puissance)
#     "climb":    2.1,   # kg/s
#     "cruise":   0.85,  # kg/s  (régime normal)
#     "descent":  0.25,  # kg/s
#     "landing":  0.3,   # kg/s
#     }
#     for phase in BASE_FUEL_FLOW:
#         fuel_burn_rate_kg_per_s += BASE_FUEL_FLOW[phase] * (0.75 + 0.25 * load_factor)
    
#     trip_fuel = fuel_burn_rate_kg_per_s * (flight_time_h / 36000)

#     total_fuel  = trip_fuel * 1.15

#     # TSFC  = Thrust Specific Fuel Consumption (consommation spécifique)
#     #         ≈ 0.000015 à 0.000018 kg/(N·s) pour un turbofan moderne
#     # L/D   = Lift-to-Drag ratio (finesse aérodynamique)
#     #         ≈ 17-18 pour un A320, ≈ 19-21 pour un B777
#     # speed = vitesse de croisière en km/h (≈ 900 km/h soit Mach 0.82)