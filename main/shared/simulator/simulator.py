import time
from airport.application.runway_assignment_service import assign_flight_to_departure_runway
from shared.simulator.departure_simulator.departure import _tick_runway
from shared.simulator.flight_simulator.flight import _tick_flight
from shared.simulator.landing_simulator.landing import _tick_landing
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