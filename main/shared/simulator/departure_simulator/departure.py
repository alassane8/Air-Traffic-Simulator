import math
from typing import List

from airport.application.taxiway_pathfinding_service import find_path_graph
from flight.application.flight_service import advance_status, is_departing
from flight.application.flight_timing_service import init_flight_cruising_time, init_flight_estimated_arrival_time
from flight.domain.flight import Flight, FlightStatus
from air_corridor.domain.air_corridor import AirCorridor
from aircraft.domain.aircraft import Aircraft
from airport.domain.enums.node_status import NodeStatus
from shared.simulator.departure_simulator.compute_fuel import compute_flight_fuel
from shared.simulator.departure_simulator.takeoff import _do_takeoff
from aircraft.domain.aircraft_type import AircraftType

def init_aircraft_boarding(
    aircraft: Aircraft,
    flight: Flight,
    air_corridors: dict,
) -> None:
    """
    Initialise l'avion et le vol au moment du boarding
      - charge le carburant calculé dans flight.fuel_kg
      - fixe flight.fuel_burn_rate_kg_per_s (utilisé par update_flight_fuel)
    """
    import datetime as _dt

    total_fuel_kg, burn_rate = compute_flight_fuel(aircraft, flight, air_corridors)

    flight.fuel_kg = total_fuel_kg
    flight.fuel_burn_rate_kg_per_s = burn_rate

    aircraft.updated_at = _dt.datetime.now()


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
            if is_departing(f) and f.depart_airport_id == depart_runway.airport_id
        ]

        if not departure_queue or departure_queue[0] != flight:
            continue

        if flight.status == FlightStatus.PLANNED:
            advance_status(flight)
            flight.time_spent = 0

        elif flight.status == FlightStatus.BOARDING:
            if flight.time_spent == 0:
                aircraft = aircrafts.get(flight.aircraft_id)
                if aircraft:
                    init_aircraft_boarding(aircraft, flight, air_corridors)
                else:
                    print(f"[WARN] boarding {flight.flight_code} : aircraft introuvable (id={flight.aircraft_id})")
            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.BOARDING.duration_seconds:
                advance_status(flight)
                flight.time_spent = 0

        elif flight.status == FlightStatus.LINEUP:
            if flight.time_spent == 0:
                gate = gates.get(flight.depart_gate_code)
                if gate and gate in occupied_gates:
                    occupied_gates.remove(gate)
                    gate.release_aircraft()
                    terminal = terminals.get(gate.terminal)
                    if terminal:
                        terminal.remove_plane()

            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.LINEUP.duration_seconds:
                advance_status(flight)
                flight.time_spent = 0

        elif flight.status == FlightStatus.TAKEOFF:
            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.TAKEOFF.duration_seconds:
                _do_takeoff(flight, depart_runway, active_flights, new_departures, airports, air_corridors)
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
    opened_nodes = {n.id: n for n in nodes.values() if n.status == NodeStatus.OPEN}

    for node in opened_nodes.values():
        if node.ref == flight.depart_gate_code:
            start_id = node.id
        elif node.ref == flight.depart_runway_code:
            goal_id = node.id

    if not start_id or not goal_id:
        raise ValueError(
            f"Gate '{flight.depart_gate_code}' ou runway '{flight.depart_runway_code}' introuvable"
        )

    return find_path_graph(opened_nodes, edges, start_id, goal_id)