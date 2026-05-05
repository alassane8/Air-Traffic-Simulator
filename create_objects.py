from datetime import datetime
import random
import uuid

from aircraft import Aircraft, AircraftType
from airport import Airport
from air_corridor import AirCorridor, CorridorDirection, CorridorStatus
from edge import Edge
from node import Node, NodeStatus
from terminal import Terminal, TerminalStatus
from gate import Gate, GateStatus
from airline import Airline
from runway import Runway, RunwayStatus
from waypoint import Waypoint, WaypointStatus


def create_aircrafts(aircraftsData: dict)-> Aircraft:
    allAircrafts = {}

    for aircraft in aircraftsData.get("aircrafts", []):
        object = Aircraft(
            aircraft.get("id", uuid.uuid4()),
            aircraft.get("aircraft_code", "NULL"),
            aircraft.get("seats", 0),
            aircraft.get("passengers", 0),
            aircraft.get("aircraft_type", random.choice(list(AircraftType))),
            aircraft.get("maximum_speed", 800),
            aircraft.get("cruising_speed", 700),
            aircraft.get("created_at", datetime.now),
            aircraft.get("updated_at", datetime.now),
        )

        allAircrafts[aircraft.get("id")] = object

    return allAircrafts


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_airports(airportsData: dict) -> Airport:
    allAirports = {}

    for airport in airportsData.get('airports', []):
        object = Airport(
            airport.get("id", uuid.uuid4()),
            airport.get("airport_code", "NULL"),
            airport.get("lat", "NULL"),
            airport.get("lon", "NULL"),
            airport.get("terminals", []),
            airport.get("gates", []),
            airport.get("runways", []),
            airport.get("taxiway_graph", []),
            airport.get("created_at", datetime.now),
            airport.get("updated_at", datetime.now),
        )

        allAirports[airport.get("id")] = object

    return allAirports


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_terminals(airportsData: dict) -> Terminal:
    allTerminals = {}

    for airport in airportsData.get('airports', []):
        for terminal in airport.get('terminals', []):
            object = Terminal(
                terminal.get("id", uuid.uuid4()),
                terminal.get("terminal_code", "NULL"),
                terminal.get("terminal_airport", "NULL"),
                terminal.get("max_planes", 20),
                terminal.get("planes_on_deck", 0),
                terminal.get("status", TerminalStatus.OPEN),
                terminal.get("created_at", datetime.now),
                terminal.get("updated_at", datetime.now),
            )

            allTerminals[terminal.get("id")] = object

    return allTerminals


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_airlines(airlinesData: dict) -> Airline:
    allAirlines = {}

    for airline in airlinesData.get('airlines', []):
        object = Airline(
            airline.get("id", uuid.uuid4()),
            airline.get("name", "NULL"),
            airline.get("iata_code", "NULL"),
            airline.get("icao_code", "NULL"),
            airline.get("country", "NULL"),
            airline.get("created_at", datetime.now),
            airline.get("updated_at", datetime.now),
        )

        allAirlines[airline.get("id")] = object

    return allAirlines


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_gates(airportsData: dict) -> Gate:
    allGates = {}

    for airport in airportsData.get('airports', []):
        for gate in airport.get('gates', []):
            object = Gate(
                gate.get("id", uuid.uuid4()),
                gate.get("gate_code", "NULL"),
                gate.get("terminal", "NULL"),
                gate.get("aircraft_id", "NULL"),
                gate.get("status", GateStatus.FREE),
                gate.get("created_at", datetime.now),
                gate.get("updated_at", datetime.now)
            )

            allGates[gate.get("id")] = object

    return allGates


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_runways(airportsData: dict) -> Runway:
    allRunways = {}

    for airport in airportsData.get('airports', []):
        for runway in airport.get('runways', []):
            object = Runway(
                runway.get("id", uuid.uuid4()),
                runway.get("airport_id", "NULL"),
                runway.get("length", "NULL"),
                runway.get("heading", "NULL"),
                runway.get("status", RunwayStatus.FREE),
                runway.get("current_aircraft", None),
                runway.get("scheduled_flights", []),
                runway.get("created_at", datetime.now),
                runway.get("updated_at", datetime.now)
            )

            allRunways[runway.get("id")] = object

    return allRunways


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_air_corridors(airCorridorsData: dict) -> AirCorridor:
    allAirCorridors = {}

    for airCorridor in airCorridorsData.get('air_corridors', []):
        object = AirCorridor(
            airCorridor.get("id", uuid.uuid4()),
            airCorridor.get("air_corridor_code", "NULL"),
            airCorridor.get("from_airport", "NULL"),
            airCorridor.get("to_airport", "NULL"),
            airCorridor.get("distance", "NULL"),
            airCorridor.get("altitude", "NULL"),
            airCorridor.get("direction", CorridorDirection.BIDIRECTIONAL),
            airCorridor.get("status", CorridorStatus.OPEN),
            airCorridor.get("max_capacity", 20),
            airCorridor.get("aircrafts", []),
            airCorridor.get("waypoints", []),
            airCorridor.get("created_at", datetime.now),
            airCorridor.get("updated_at", datetime.now)
        )

        allAirCorridors[airCorridor.get("id")] = object

    return allAirCorridors


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_waypoints(airCorridorsData: dict) -> Waypoint:
    allWaypoints = {}

    
    for airCorridor in airCorridorsData.get('air_corridors', []):
        for waypoint in airCorridor.get('waypoints', []):
            object = Waypoint(
                waypoint.get("id", uuid.uuid4()),
                waypoint.get("lat", "NULL"),
                waypoint.get("lon", "NULL"),
                waypoint.get("min_alt_ft", "NULL"),
                waypoint.get("max_alt_ft", "NULL"),
                waypoint.get("status", WaypointStatus.OPEN),
                waypoint.get("created_at", datetime.now),
                waypoint.get("updated_at", datetime.now)
            )

            allWaypoints[waypoint.get("id")] = object

    return allWaypoints


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def create_edges(airportsData: dict) -> Edge:
    allEdges = {}

    for airport in airportsData.get('airports', []):
        for edge in airport.get('taxiway_graph', {}).get('edges', []):
            object = Edge(
                edge.get("id", str(uuid.uuid4())),
                edge.get("from_node_id", "NULL"),
                edge.get("to_node_id", "NULL"),
                edge.get("taxiway", "NULL"),
                edge.get("distance_m", "NULL"),
                edge.get("created_at", datetime.now),
                edge.get("updated_at", datetime.now)
            )
            allEdges[object.id] = object

    return allEdges


def create_nodes(airportsData: dict) -> Node:
    allNodes = {}

    for airport in airportsData.get('airports', []):
        for node in airport.get('taxiway_graph', {}).get('nodes', []):
            object = Node(
                node.get("id", str(uuid.uuid4())),
                node.get("type", "NULL"),
                node.get("ref", "NULL"),
                node.get("lat", "NULL"),
                node.get("lon", "NULL"),
                node.get("status", NodeStatus.OPEN),
                node.get("created_at", datetime.now),
                node.get("updated_at", datetime.now)
            )
            allNodes[object.id] = object

    return allNodes


def update_airports_with_runways(airports: dict, runways: dict):
    for airport in airports.values():
        airport.runways = [r for r in runways.values() if r.airport_id == airport.id]

def update_airports_with_gates(airports: dict, gates: dict):
    for airport in airports.values():
        terminals_ids = [t.id for t in airport.terminals]
        airport.gates = [g for g in gates.values() if g.terminal in terminals_ids]

def update_airports_with_terminals(airports: dict, terminals: dict):
    for airport in airports.values():
        airport.terminals = [t for t in terminals.values() if t.airport_id == airport.id]