from datetime import datetime, timedelta

from air_corridor.domain.air_corridor import AirCorridor
from aircraft.domain.aircraft import Aircraft
from flight.domain.flight import Flight, FlightStatus


def init_flight_estimated_departure_time(scheduled_flights: list) -> None:
    for i in range(len(scheduled_flights)):
        if i == 0:
            scheduled_flights[i].estimated_departure_time = (
                datetime.now()
                + timedelta(
                    seconds=(
                        FlightStatus.PLANNED.duration_seconds
                        + FlightStatus.LINEUP.duration_seconds
                    )
                )
            )
        else:
            scheduled_flights[i].estimated_departure_time = (
                scheduled_flights[i - 1].estimated_departure_time
                + timedelta(seconds=FlightStatus.TAKEOFF.duration_seconds)
            )


def init_flight_cruising_time(aircraft: Aircraft, corridor: AirCorridor, time_scale: float) -> float:
    speed_km_s = aircraft.cruising_speed / 3600
    real_seconds = float(corridor.distance) / speed_km_s
    return real_seconds / time_scale


def init_flight_estimated_arrival_time(flight: Flight, cruising_time: float) -> datetime:
    return flight.departure_time + timedelta(
        seconds=(
            FlightStatus.CLIMBING.duration_seconds
            + cruising_time
            + FlightStatus.DESCENDING.duration_seconds
            + FlightStatus.LANDING.duration_seconds
            + FlightStatus.TAXI.duration_seconds
        )
    )
