from datetime import datetime
import random
import uuid

from aircraft.domain.aircraft import Aircraft, AircraftType
from airline.domain.airline import Airline
from air_corridor.domain.air_corridor import AirCorridor, CorridorDirection, CorridorStatus
from airport.domain.airport import Airport
from airport.domain.edge import Edge
from airport.domain.gate import Gate, GateStatus
from airport.domain.node import Node, NodeStatus
from airport.domain.runway import Runway, RunwayStatus
from airport.domain.terminal import Terminal, TerminalStatus
from waypoint.domain.waypoint import Waypoint, WaypointStatus


def create_aircrafts(aircrafts_data: dict) -> dict:
    all_aircrafts = {}
    for aircraft in aircrafts_data.get("aircrafts", []):
        obj = Aircraft(
            aircraft.get("id", uuid.uuid4()),
            aircraft.get("aircraft_code", "NULL"),
            aircraft.get("seats", 0),
            aircraft.get("passengers", 0),
            aircraft.get("aircraft_type", random.choice(list(AircraftType))),
            aircraft.get("maximum_speed", 800),
            aircraft.get("cruising_speed", 700),
            aircraft.get("operating_empty_weight_kg", 0),
            aircraft.get("maximum_total_operating_weight_kg", 0),
            aircraft.get("max_fuel_kg", 0),
            aircraft.get("fuel_flow_cruise_kg_per_s", 0),
            aircraft.get("wing_area_m2", 0),
            aircraft.get("ld_ratio", 0),
            aircraft.get("created_at", datetime.now()),
            aircraft.get("updated_at", datetime.now()),
        )
        all_aircrafts[aircraft.get("id")] = obj
    return all_aircrafts


def create_airports(airports_data: dict) -> dict:
    all_airports = {}
    for airport in airports_data.get("airports", []):
        obj = Airport(
            airport.get("id", uuid.uuid4()),
            airport.get("airport_code", "NULL"),
            airport.get("lat", "NULL"),
            airport.get("lon", "NULL"),
            airport.get("terminals", []),
            airport.get("gates", []),
            airport.get("runways", []),
            airport.get("taxiway_graph", []),
            airport.get("created_at", datetime.now()),
            airport.get("updated_at", datetime.now()),
        )
        all_airports[airport.get("id")] = obj
    return all_airports


def create_terminals(airports_data: dict) -> dict:
    all_terminals = {}
    for airport in airports_data.get("airports", []):
        for terminal in airport.get("terminals", []):
            obj = Terminal(
                terminal.get("id", uuid.uuid4()),
                terminal.get("terminal_code", "NULL"),
                terminal.get("terminal_airport", "NULL"),
                terminal.get("max_planes", 20),
                terminal.get("planes_on_deck", 0),
                terminal.get("status", TerminalStatus.OPEN),
                terminal.get("created_at", datetime.now()),
                terminal.get("updated_at", datetime.now()),
            )
            all_terminals[terminal.get("id")] = obj
    return all_terminals


def create_airlines(airlines_data: dict) -> dict:
    all_airlines = {}
    for airline in airlines_data.get("airlines", []):
        obj = Airline(
            airline.get("id", uuid.uuid4()),
            airline.get("name", "NULL"),
            airline.get("iata_code", "NULL"),
            airline.get("icao_code", "NULL"),
            airline.get("country", "NULL"),
            airline.get("created_at", datetime.now()),
            airline.get("updated_at", datetime.now()),
        )
        all_airlines[airline.get("id")] = obj
    return all_airlines


def create_gates(airports_data: dict) -> dict:
    all_gates = {}
    for airport in airports_data.get("airports", []):
        for gate in airport.get("gates", []):
            obj = Gate(
                gate.get("id", uuid.uuid4()),
                gate.get("gate_code", "NULL"),
                gate.get("terminal", "NULL"),
                gate.get("aircraft_id", "NULL"),
                gate.get("status", GateStatus.FREE),
                gate.get("created_at", datetime.now()),
                gate.get("updated_at", datetime.now()),
            )
            all_gates[gate.get("id")] = obj
    return all_gates


def create_runways(airports_data: dict) -> dict:
    all_runways = {}
    for airport in airports_data.get("airports", []):
        for runway in airport.get("runways", []):
            obj = Runway(
                runway.get("id", uuid.uuid4()),
                runway.get("airport_id", "NULL"),
                runway.get("length", "NULL"),
                runway.get("heading", "NULL"),
                runway.get("status", RunwayStatus.FREE),
                runway.get("current_aircraft", None),
                runway.get("scheduled_flights", []),
                runway.get("created_at", datetime.now()),
                runway.get("updated_at", datetime.now()),
            )
            all_runways[runway.get("id")] = obj
    return all_runways

def create_waypoints(air_corridors_data: dict) -> dict:
    all_waypoints = {}

    for corridor in air_corridors_data.get("air_corridors", []):
        for waypoint in corridor.get("waypoints", []):

            waypoint_id= (f"{corridor['id']}_{waypoint['id']}")

            if waypoint_id in all_waypoints:
                continue

            obj = Waypoint(
                waypoint_id,
                waypoint.get("lat"),
                waypoint.get("lon"),
                waypoint.get("min_alt_ft"),
                waypoint.get("max_alt_ft"),
                waypoint.get("status", WaypointStatus.OPEN),
                waypoint.get("created_at", datetime.now()),
                waypoint.get("updated_at", datetime.now()),
            )

            all_waypoints[waypoint_id] = obj

    return all_waypoints


def create_air_corridors(
    air_corridors_data: dict,
    all_waypoints: dict
) -> dict:

    all_air_corridors = {}

    for corridor in air_corridors_data.get("air_corridors", []):
        corridor_waypoints = []

        for waypoint_data in corridor.get("waypoints", []):
            waypoint_id = waypoint_data.get("id")

            if waypoint_id in all_waypoints:
                corridor_waypoints.append(all_waypoints[waypoint_id])

        obj = AirCorridor(
            corridor.get("id", str(uuid.uuid4())),
            corridor.get("air_corridor_code"),
            corridor.get("from_airport"),
            corridor.get("to_airport"),
            corridor.get("distance"),
            corridor.get("altitude"),
            corridor.get("direction",CorridorDirection.BIDIRECTIONAL),
            corridor.get("status",CorridorStatus.OPEN),
            corridor.get("max_capacity", 20),
            corridor.get("aircrafts", []),
            corridor_waypoints,
            corridor.get("created_at",datetime.now()),
            corridor.get("updated_at",datetime.now()),
        )

        all_air_corridors[corridor.get("id")] = obj

    return all_air_corridors

def create_edges(airports_data: dict) -> dict:
    all_edges = {}
    for airport in airports_data.get("airports", []):
        for edge in airport.get("taxiway_graph", {}).get("edges", []):
            obj = Edge(
                edge.get("id", str(uuid.uuid4())),
                edge.get("from_node_id", "NULL"),
                edge.get("to_node_id", "NULL"),
                edge.get("taxiway", "NULL"),
                edge.get("distance_m", "NULL"),
                edge.get("created_at", datetime.now()),
                edge.get("updated_at", datetime.now()),
            )
            all_edges[obj.id] = obj
    return all_edges


def create_nodes(airports_data: dict) -> dict:
    all_nodes = {}
    for airport in airports_data.get("airports", []):
        for node in airport.get("taxiway_graph", {}).get("nodes", []):
            obj = Node(
                node.get("id", str(uuid.uuid4())),
                node.get("type", "NULL"),
                node.get("ref", "NULL"),
                node.get("lat", "NULL"),
                node.get("lon", "NULL"),
                node.get("status", NodeStatus.OPEN),
                node.get("created_at", datetime.now()),
                node.get("updated_at", datetime.now()),
            )
            all_nodes[obj.id] = obj
    return all_nodes


def update_airports_with_runways(airports: dict, runways: dict) -> None:
    for airport in airports.values():
        airport.runways = [r for r in runways.values() if r.airport_id == airport.id]


def update_airports_with_gates(airports: dict, gates: dict) -> None:
    for airport in airports.values():
        terminal_ids = [t.id for t in airport.terminals]
        airport.gates = [g for g in gates.values() if g.terminal in terminal_ids]


def update_airports_with_terminals(airports: dict, terminals: dict) -> None:
    for airport in airports.values():
        airport.terminals = [t for t in terminals.values() if t.airport_id == airport.id]
