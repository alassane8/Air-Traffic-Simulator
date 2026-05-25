import time

from shared.simulator import simulator
from shared import object_factory
from shared.bootstrap import init_simulator_data
from airport.application.gate_assignment_service import assign_aircrafts_to_gates


def main() -> int:
    airports, terminals, gates, runways, aircrafts, waypoints, air_corridors, airlines, edges, nodes = init_simulator_data()

    object_factory.update_airports_with_terminals(airports, terminals)
    object_factory.update_airports_with_gates(airports, gates)
    object_factory.update_airports_with_runways(airports, runways)

    occupied_gates = assign_aircrafts_to_gates(aircrafts, gates, terminals)

    simulator.run_simulation(
        terminals, waypoints, aircrafts, airports,
        air_corridors, airlines, runways, occupied_gates,
        edges, nodes, gates,
    )
    return 0


if __name__ == "__main__":
    main()