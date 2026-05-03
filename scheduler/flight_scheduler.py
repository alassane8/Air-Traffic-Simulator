from datetime import datetime
import random

from aircraft import AircraftType
from flight import Flight, RunwayUsageType
from scheduler.corridor_manager import initCorridor
from scheduler.flight_sorter import sortFlightsByPriority
from scheduler.flight_timing import initFlightCruisingTime, initFlightEstimatedArrivalTime, initFlightEstimatedDepartureTime
from scheduler.fligth_factory import creatingFlight
from scheduler.runway_manager import initRunwayArrival


def schedule_flights(terminals: dict, aircrafts: dict, airlines: dict, runways: dict, occupied_gates: list) -> dict:
    
    allFlights = {}

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
        created_Flight = creatingFlight(airline, gate, terminals, choosed_runway_id)
        allFlights[created_Flight.id] = created_Flight
        choosed_runway.scheduled_flights.append(created_Flight)
        

    return allFlights


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def scheduler(runways: dict, airports: dict, aircrafts: dict, airCorridors: dict):
    
    for runway in runways.values():
        scheduled_flights = runway.scheduled_flights
        sorted_scheduled_flights = sortFlightsByPriority(scheduled_flights)

        initFlightEstimatedDepartureTime(sorted_scheduled_flights)

        for flight in sorted_scheduled_flights:
            air_corridor = initCorridor(airCorridors, flight.depart_terminal_code, airports, flight.aircraft_code)
            
            if air_corridor is None:
                print(f"[WARN] Aucun corridor pour le vol {flight.flight_code} depuis {flight.depart_terminal_code}")
                continue
            
            flight.corridor_code = air_corridor.air_corridor_code
            flight.arrival_airport_code = air_corridor.to_airport

            aircraft = aircrafts[flight.aircraft_code]
            cruising_time = initFlightCruisingTime(aircraft, air_corridor)
            flight.estimated_arrival_time = initFlightEstimatedArrivalTime(flight, cruising_time)

            arrival_runway = initRunwayArrival(air_corridor, airports, flight)
            flight.arrival_runway_code = arrival_runway.id

        for runway in runways.values():
            runway.scheduled_flights.sort(
                key=lambda f: (
                    f.estimated_departure_time if f.runway_usage == RunwayUsageType.DEPARTURE
                    else f.estimated_arrival_time
                ) or datetime.max
            )