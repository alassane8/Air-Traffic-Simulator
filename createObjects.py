from aircraft import Aircraft
from airport import Airport
from airCorridor import AirCorridor
from terminal import Terminal
from gate import Gate
from airline import Airline
from runway import Runway


def createAircrafts(aircraftsData: dict)-> Aircraft:
    allAircrafts = {}

    for aircraft in aircraftsData.get("aircrafts", []):
        object = Aircraft(
            aircraft.get("id", "NULL"),
            aircraft.get("aircraft_code", "NULL"),
            aircraft.get("seats", "NULL"),
            aircraft.get("passengers", "NULL"),
            aircraft.get("aircraft_type", "NULL"),
            aircraft.get("cruising_speed", "NULL"),
            aircraft.get("created_at", "NULL"),
            aircraft.get("updated_at", "NULL")
        )

        allAircrafts[aircraft.get("id")] = object

    return allAircrafts


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def createAirports(airportsData: dict) -> Airport:
    allAirports = {}

    for airport in airportsData.get('airports', []):
        object = Airport(
            airport.get("id", "NULL"),
            airport.get("airport_code", "NULL"),
            airport.get("lat", "NULL"),
            airport.get("long", "NULL"),
            airport.get("created_at", "NULL"),
            airport.get("updated_at", "NULL"),
            airport.get("terminals", "NULL"),
            airport.get("runways", "NULL"),
            airport.get("gates", "NULL")
        )

        allAirports[airport.get("id")] = object

    return allAirports


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def createTerminals(airportsData: dict) -> Terminal:
    allTerminals = {}

    for airport in airportsData.get('airports', []):
        for terminal in airport.get('terminals', []):
            object = Terminal(
                terminal.get("id", "NULL"),
                terminal.get("terminal_code", "NULL"),
                terminal.get("terminal_airport", "NULL"),
                terminal.get("max_planes", "NULL"),
                terminal.get("planes_on_deck", 0),
                terminal.get("status", "OPEN"),
                terminal.get("created_at", "NULL"),
                terminal.get("updated_at", "NULL"),
            )

            allTerminals[terminal.get("id")] = object

    return allTerminals


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def createAirlines(airlinesData: dict) -> Airline:
    allAirlines = {}

    for airline in airlinesData.get('airlines', []):
        object = Airline(
            airline.get("id", "NULL"),
            airline.get("name", "NULL"),
            airline.get("iata_code", "NULL"),
            airline.get("icao_code", "NULL"),
            airline.get("country", "NULL"),
            airline.get("created_at", "NULL"),
            airline.get("updated_at", "NULL"),
        )

        allAirlines[airline.get("id")] = object

    return allAirlines


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def createGates(airportsData: dict) -> Gate:
    allGates = {}

    for airport in airportsData.get('airports', []):
        for gate in airport.get('gates', []):
            object = Gate(
                gate.get("id", "NULL"),
                gate.get("gate_code", "NULL"),
                gate.get("terminal", "NULL"),
                gate.get("aircraft_id", "NULL"),
                gate.get("status", "FREE"),
                gate.get("created_at", "NULL"),
                gate.get("updated_at", "NULL")
            )

            allGates[gate.get("id")] = object

    return allGates


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def createRunways(airportsData: dict) -> Runway:
    allRunways = {}

    for airport in airportsData.get('airports', []):
        for runway in airport.get('runways', []):
            object = Runway(
                runway.get("id", "NULL"),
                runway.get("airport_id", "NULL"),
                runway.get("length", "NULL"),
                runway.get("heading", "NULL"),
                runway.get("status", "FREE"),
                runway.get("current_aircraft", None),
                runway.get("scheduled_flights", []),
                runway.get("created_at", "NULL"),
                runway.get("updated_at", "NULL")
            )

            allRunways[runway.get("id")] = object

    return allRunways


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def createAirCorridors(airCorridorsData: dict) -> AirCorridor:
    allAirCorridors = {}

    for airCorridor in airCorridorsData.get('air_corridors', []):
        object = AirCorridor(
            airCorridor.get("id", "NULL"),
            airCorridor.get("air_corridor_code", "NULL"),
            airCorridor.get("from_airport", "NULL"),
            airCorridor.get("to_airport", "NULL"),
            airCorridor.get("aircrafts", []),
            airCorridor.get("altitude", "NULL"),
            airCorridor.get("distance", "NULL"),
            airCorridor.get("direction", "BIDIRECTIONAL"),
            airCorridor.get("status", "OPEN"),
            airCorridor.get("max_capacity", "NULL"),
            airCorridor.get("created_at", "NULL"),
            airCorridor.get("updated_at", "NULL")
        )

        allAirCorridors[airCorridor.get("id")] = object

    return allAirCorridors