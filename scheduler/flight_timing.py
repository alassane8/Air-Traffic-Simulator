from datetime import datetime, timedelta

from air_corridor import AirCorridor
from aircraft import Aircraft
from flight import Flight, FlightStatus


def initFlightEstimatedDepartureTime(scheduled_flights: list) -> datetime:
    for flight in range(len(scheduled_flights)):
        if flight == 0:
            scheduled_flights[flight].estimated_departure_time = datetime.now() + timedelta(seconds=FlightStatus.PLANNED.duration_seconds +
                                                                                        FlightStatus.BOARDING.duration_seconds +
                                                                                        FlightStatus.LINEUP.duration_seconds)
        else:
            scheduled_flights[flight].estimated_departure_time = scheduled_flights[flight - 1].estimated_departure_time + timedelta(seconds=FlightStatus.TAKEOFF.duration_seconds)
        
    return None

def initFlightCruisingTime(aircraft: Aircraft, corridor: AirCorridor) -> float:
    return float(corridor.distance) / float(aircraft.maximum_speed)


def initFlightEstimatedArrivalTime(flight: Flight, cruising_time: datetime) -> datetime:
    return flight.estimated_departure_time + timedelta(seconds=FlightStatus.CLIMBING.duration_seconds + 
                                                       cruising_time + 
                                                       FlightStatus.DESCENDING.duration_seconds + 
                                                       FlightStatus.LANDING.duration_seconds)


