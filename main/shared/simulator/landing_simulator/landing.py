

from airport.application.gate_assignment_service import find_best_landing_gate
from airport.application.runway_assignment_service import assign_arrival_runway, assign_flight_to_departure_runway
from flight.application.flight_service import advance_status
from flight.domain.flight import FlightStatus
from shared.simulator.landing_simulator.descent import _do_land


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
