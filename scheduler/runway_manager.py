from datetime import datetime
import random
import copy

from air_corridor import AirCorridor
from aircraft import AircraftType
from airport import Airport
from flight import Flight, FlightStatus, RunwayUsageType
from flight_helpers import isDeparting, sortByPriority
from scheduler.corridor_manager import initCorridor
from scheduler.flight_timing import initFlightCruisingTime, initFlightEstimatedArrivalTime, initFlightEstimatedDepartureTime
from scheduler.fligth_factory import creatingFlight


def assign_flight_to_departure_runway(terminals: dict, aircrafts: dict, airlines: dict, runways: dict, occupied_gates: list, edges: dict, nodes: dict) -> dict:
    
    departure_flights = {}

    for gate in occupied_gates:
        terminal = terminals[gate.terminal]
        airport_id = terminal.airport_id
        airport_runways = {}
        aircraft = aircrafts.get(gate.aircraft_id)
        airline = random.choice(list(airlines.values()))
        aircraft_type = aircraft.aircraft_type

        for runway in runways.values():
            if runway.airport_id == airport_id:
                airport_runways[runway.id] = runway

        shortest_runway = min(airport_runways.values(), key=lambda runway: runway.length)
        longest_runway = max(airport_runways.values(), key=lambda runway: runway.length)

        if aircraft_type == AircraftType.NARROW:
            choosed_runway = random.choice(list(airport_runways.values()))
            
        elif aircraft_type == AircraftType.LARGE:
            eligible = [r for r in airport_runways.values() if r.id != shortest_runway.id]
            choosed_runway = random.choice(eligible)
            
        else:
            choosed_runway = longest_runway
            
        choosed_runway_id = choosed_runway.id
        created_flight = creatingFlight(airline, gate, terminals, choosed_runway_id)
        departure_flights[created_flight.id] = created_flight
        choosed_runway.add_flight(created_flight)
        created_flight.status = FlightStatus.PLANNED

    return departure_flights


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def assign_flight_to_arrival_runway(runways: dict, airports: dict, aircrafts: dict, airCorridors: dict):
    
    for runway in runways.values():
        scheduled_flights = runway.scheduled_flights
        departure_flights = [f for f in scheduled_flights if isDeparting(f)]
        sorted_scheduled_flights = sortByPriority(departure_flights)

        initFlightEstimatedDepartureTime(sorted_scheduled_flights)

        for flight in sorted_scheduled_flights:
            air_corridor = initCorridor(airCorridors, flight.depart_terminal_code, airports, flight.aircraft_code)
            
            if air_corridor is None:
                print(f"[WARN] Aucun corridor pour {flight.flight_code}")
                continue

            flight.corridor_code = air_corridor.air_corridor_code
            flight.arrival_airport_code = air_corridor.to_airport
            flight.dest_lat = get_arrival_airport_lat(flight, airports)
            flight.dest_lon = get_arrival_airport_lon(flight, airports)

            aircraft = aircrafts[flight.aircraft_code]
            cruising_time = initFlightCruisingTime(aircraft, air_corridor)
            flight.estimated_arrival_time = initFlightEstimatedArrivalTime(flight, cruising_time)

            arrival_runway = initRunwayArrival(air_corridor, airports, flight)
            flight.arrival_runway_code = arrival_runway.id

        for runway in runways.values():
            runway.scheduled_flights.sort(
                key=lambda f: (
                    f.estimated_departure_time if isDeparting(f)
                    else f.estimated_arrival_time
                ) or datetime.max
            )


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
            
def initRunwayArrival(airCorridor: AirCorridor, airports: dict, flight: Flight):
    arrival_airport = airports[airCorridor.to_airport]

    # Vérifier si le vol est déjà schedulé sur une runway d'arrivée
    for runway in arrival_airport.runways:
        if any(f.id == flight.id for f in runway.scheduled_flights):
            return runway  # déjà assigné, rien à faire

    # Première fois — on assigne
    arrival_runway = random.choice(arrival_airport.runways)
    flight.runway_usage = RunwayUsageType.ARRIVAL  # on modifie le vol original, pas une copie
    arrival_runway.add_flight(flight)

    return arrival_runway

def get_arrival_airport_lat(flight: Flight, airports: dict[Airport]) -> str:

    for airport in airports.values():
        if airport.id == flight.arrival_airport_code:
            return airport.lat
    return None


def get_arrival_airport_lon(flight: Flight, airports: dict[Airport]) -> str:

    for airport in airports.values():
        if airport.id == flight.arrival_airport_code:
            return airport.lon
    return None
