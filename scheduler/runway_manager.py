from datetime import datetime
import random

from air_corridor import AirCorridor
from aircraft import AircraftType
from airport import Airport
from flight import Flight, FlightStatus, RunwayUsageType
from flight_helpers import isDeparting, sortByPriority
from scheduler.corridor_manager import initCorridor
from scheduler.flight_timing import initFlightCruisingTime, initFlightEstimatedArrivalTime, initFlightEstimatedDepartureTime
from scheduler.fligth_factory import creatingFlight


# ── DÉPART ───────────────────────────────────────────────────────────────────

def assign_flight_to_departure_runway(
    terminals: dict, aircrafts: dict, airlines: dict, runways: dict,
    occupied_gates: list, airports: dict, airCorridors: dict
) -> dict:
    """
    Crée les vols de départ, les assigne à une runway de départ,
    et initialise le corridor + aéroport d'arrivée.
    La runway d'arrivée sera choisie pendant le cruise.
    """
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

        if not airport_runways:
            continue

        shortest_runway = min(airport_runways.values(), key=lambda r: r.length)
        longest_runway  = max(airport_runways.values(), key=lambda r: r.length)

        if aircraft_type == AircraftType.NARROW:
            chosen_runway = random.choice(list(airport_runways.values()))
        elif aircraft_type == AircraftType.LARGE:
            eligible = [r for r in airport_runways.values() if r.id != shortest_runway.id]
            chosen_runway = random.choice(eligible) if eligible else longest_runway
        else:
            chosen_runway = longest_runway

        created_flight = creatingFlight(airline, gate, terminals, chosen_runway.id)

        # Initialiser le corridor et la destination (sans runway d'arrivée)
        air_corridor = initCorridor(airCorridors, gate.terminal, airports, aircraft)
        if air_corridor is None:
            print(f"[WARN] Aucun corridor pour le vol depuis {gate.id}")
            continue

        created_flight.corridor_code         = air_corridor.air_corridor_code
        created_flight.arrival_airport_code  = air_corridor.to_airport
        created_flight.dest_lat              = _get_airport_lat(created_flight.arrival_airport_code, airports)
        created_flight.dest_lon              = _get_airport_lon(created_flight.arrival_airport_code, airports)
        created_flight.status                = FlightStatus.PLANNED

        chosen_runway.add_flight(created_flight)
        departure_flights[created_flight.id] = created_flight

    # Trier chaque runway de départ par priorité et calculer les heures estimées
    for runway in runways.values():
        dep_flights = sortByPriority([
            f for f in runway.scheduled_flights
            if isDeparting(f) and f.depart_airport_code == runway.airport_id
        ])
        initFlightEstimatedDepartureTime(dep_flights)
        runway.scheduled_flights.sort(
            key=lambda f: f.estimated_departure_time or datetime.max
        )

    return departure_flights


# ── ARRIVÉE (appelé pendant le CRUISE) ───────────────────────────────────────

def assign_arrival_runway(flight: Flight, airports: dict) -> bool:
    """
    Choisit la runway d'arrivée pour un vol en cruise.
    Appelé depuis schedule.py une seule fois par vol.
    Retourne True si une runway a été assignée.
    """
    if flight.arrival_runway_code:
        return True  # déjà assignée

    arrival_airport = airports.get(flight.arrival_airport_code)
    if not arrival_airport or not arrival_airport.runways:
        print(f"[WARN] Aucun aéroport ou runway d'arrivée pour {flight.flight_code}")
        return False

    available = [r for r in arrival_airport.runways if r.can_schedule()]
    if not available:
        return False

    # Runway avec le moins de vols en attente = moins chargée
    chosen = min(available, key=lambda r: len(r.scheduled_flights))
    flight.arrival_runway_code = chosen.id
    flight.runway_usage = RunwayUsageType.ARRIVAL

    chosen.add_flight(flight)
    chosen.scheduled_flights.sort(
        key=lambda f: f.estimated_arrival_time or datetime.max
    )

    return True


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _get_airport_lat(airport_id: str, airports: dict) -> float:
    airport = airports.get(airport_id)
    if airport is None:
        raise ValueError(f"Aéroport '{airport_id}' introuvable dans airports dict")
    return airport.lat

def _get_airport_lon(airport_id: str, airports: dict) -> float:
    airport = airports.get(airport_id)
    if airport is None:
        raise ValueError(f"Aéroport '{airport_id}' introuvable dans airports dict")
    return airport.lon