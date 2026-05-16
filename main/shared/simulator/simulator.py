import time
import os
import sys
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
    TIME_SCALE = 20
    TICK_INTERVAL = 1.0
    SIM_TICK = TICK_INTERVAL * TIME_SCALE
    active_flights = []
    tick_count = 0

    new_departures = assign_flight_to_departure_runway(
        terminals, aircrafts, airlines, runways, occupied_gates,
        airports, air_corridors
    )

    # ── Initialisation du visualizer ──────────────────────────────
    try:
        import json
        _here = os.path.dirname(os.path.abspath(__file__))
        _root = os.path.abspath(os.path.join(_here, "..", "..", ".."))
        airports_json_path = os.path.join(_root, "main", "config", "airports.json")
        with open(airports_json_path, "r") as f:
            airports_data = json.load(f)

        from shared.adapter.visualizer.visualizer import Visualizer
        vis = Visualizer(airports_data)
        _vis_last_time = time.time() * 1000
        _vis_enabled = True
        init_logger.log("[VISUALIZER] Display active")
    except Exception as e:
        init_logger.log(f"[VISUALIZER] Could not start: {e}")
        vis = None
        _vis_enabled = False

    while True:
        tick_start = time.time()

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

        tick_count += 1

        # ── Mise à jour du visualizer ─────────────────────────────
        if _vis_enabled and vis is not None:
            now_ms = time.time() * 1000
            elapsed_ms = now_ms - _vis_last_time
            _vis_last_time = now_ms

            if not vis.handle_events():
                init_logger.log("[VISUALIZER] Window closed by user")
                vis.quit()
                vis = None
                _vis_enabled = False
            else:
                vis.update(
                    elapsed_ms,
                    tick_count  = tick_count,
                    time_scale  = TIME_SCALE,
                    flights     = list(active_flights),
                    departures  = new_departures,
                    airlines    = airlines,
                    aircrafts   = aircrafts,
                )
                vis.draw()
                vis.tick()

        elapsed = time.time() - tick_start
        time.sleep(max(0, TICK_INTERVAL - elapsed))