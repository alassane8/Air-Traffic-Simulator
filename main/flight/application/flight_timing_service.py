from datetime import datetime, timedelta
import math

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
                        + FlightStatus.BOARDING.duration_seconds
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
def compute_full_eta(flight: Flight, waypoints: list, airports: dict, time_scale: float) -> datetime:
    """
    Calcule l'ETA complète du vol en sommant la distance de tous les
    waypoints restants jusqu'à l'aéroport d'arrivée.
    """
    if flight.speed_km_h <= 0:
        return flight.estimated_arrival_time

    speed_km_s = flight.speed_km_h / 3600

    # Construire la liste des points restants à parcourir
    remaining_points = []

    # Waypoints pas encore atteints (à partir du courant)
    for wp in waypoints[flight.current_waypoint_index:]:
        remaining_points.append((wp.lat, wp.lon))

    # Aéroport d'arrivée en dernier
    arrival_airport = airports.get(flight.arrival_airport_code)
    if arrival_airport:
        remaining_points.append((arrival_airport.lat, arrival_airport.lon))

    if not remaining_points:
        return flight.estimated_arrival_time

    # Sommer les distances segment par segment
    total_km = 0.0
    prev_lat, prev_lon = flight.lat, flight.lon

    for lat, lon in remaining_points:
        lat1, lon1 = math.radians(prev_lat), math.radians(prev_lon)
        lat2, lon2 = math.radians(lat), math.radians(lon)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        a = max(0.0, min(1.0, a))
        total_km += 6371 * 2 * math.asin(math.sqrt(a))
        prev_lat, prev_lon = lat, lon

    real_seconds = (total_km / speed_km_s) / time_scale

    # Ajouter le temps de descente/landing/taxi
    real_seconds += (
        FlightStatus.DESCENDING.duration_seconds
        + FlightStatus.LANDING.duration_seconds
        + FlightStatus.TAXI.duration_seconds
    )

    return datetime.now() + timedelta(seconds=real_seconds)