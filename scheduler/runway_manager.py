import random
import copy

from airCorridor import AirCorridor
from flight import Flight, RunwayUsageType


def initRunwayArrival(airCorridor: AirCorridor, airports: dict, flight: Flight):
    arrival_airport = airports[airCorridor.to_airport]
    arrival_runway = random.choice(arrival_airport.runways)

    arrival_flight = copy.copy(flight)
    arrival_flight.runway_usage = RunwayUsageType.ARRIVAL

    arrival_runway.add_flight(arrival_flight)

    return arrival_runway