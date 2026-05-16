import random
from datetime import datetime

from aircraft.domain.aircraft import AircraftType
from flight.domain.flight import Flight, FlightStatus, RunwayUsageType
from flight.application.flight_service import is_departing, sort_by_priority
from flight.application.flight_timing_service import init_flight_estimated_departure_time
from flight.application.flight_factory import create_flight
from air_corridor.application.corridor_service import find_corridor_for_departure


# ── HELPERS INTERNES ──────────────────────────────────────────────────────────

def _find_aircraft(gate, aircrafts: dict):
    """
    Retrouve l'objet Aircraft associé à une gate.
    Essaie par id (UUID).
    """
    if gate.aircraft_id is None:
        print(f"[WARN] Aircraft introuvable pour gate {gate.id}(aircraft_id={gate.aircraft_id!r}), vol ignoré")
        return None
    else: 
        return aircrafts.get(gate.aircraft_id)


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


# ── DÉPART ────────────────────────────────────────────────────────────────────

def assign_flight_to_departure_runway(
    terminals: dict,
    aircrafts: dict,
    airlines: dict,
    runways: dict,
    occupied_gates: list,
    airports: dict,
    air_corridors: dict
) -> dict:
    """
    Crée les vols de départ, les assigne à une runway de départ,
    et initialise le corridor + aéroport d'arrivée.
    La runway d'arrivée sera choisie pendant le cruise.
    """
    departure_flights = {}

    for gate in occupied_gates:

        terminal = terminals.get(gate.terminal)
        aircraft = _find_aircraft(gate, aircrafts)

        if aircraft is None:
            continue

        airport_runways = {runway.id: runway for runway in runways.values() if runway.airport_id == terminal.airport_id}

        if not airport_runways:
            continue

        shortest_runway = min(airport_runways.values(), key=lambda r: r.length)
        longest_runway = max(airport_runways.values(), key=lambda r: r.length)

        if aircraft.aircraft_type == AircraftType.NARROW:
            chosen_runway = random.choice(list(airport_runways.values()))
        elif aircraft.aircraft_type == AircraftType.LARGE:
            eligible = [r for r in airport_runways.values() if r.id != shortest_runway.id]
            chosen_runway = random.choice(eligible) if eligible else longest_runway
        else:
            chosen_runway = longest_runway

        airline = random.choice(list(airlines.values()))
        created_flight = create_flight(airline, gate, terminals, chosen_runway.id, aircraft)

        air_corridor = find_corridor_for_departure(air_corridors, gate.terminal, airports, aircraft)
        if air_corridor is None:
            continue

        created_flight.corridor_code = air_corridor.air_corridor_code
        created_flight.arrival_airport_code = air_corridor.to_airport
        created_flight.dest_lat = _get_airport_lat(created_flight.arrival_airport_code, airports)
        created_flight.dest_lon = _get_airport_lon(created_flight.arrival_airport_code, airports)
        created_flight.status = FlightStatus.PLANNED

        chosen_runway.add_flight(created_flight)
        departure_flights[created_flight.id] = created_flight

    for runway in runways.values():
        dep_flights = sort_by_priority([
            f for f in runway.scheduled_flights
            if is_departing(f) and f.depart_airport_id == runway.airport_id
        ])
        init_flight_estimated_departure_time(dep_flights)
        runway.scheduled_flights.sort(
            key=lambda f: f.estimated_departure_time or datetime.max
        )

    return departure_flights


# ── ARRIVÉE ───────────────────────────────────────────────────────────────────

def assign_arrival_runway(flight: Flight, airports: dict) -> bool:
    """
    Choisit la runway d'arrivée pour un vol en cruise.
    Appelé depuis le simulateur une seule fois par vol.
    Retourne True si une runway a été assignée.
    """
    if flight.arrival_runway_code:
        return True

    arrival_airport = airports.get(flight.arrival_airport_code)
    if not arrival_airport or not arrival_airport.runways:
        print(f"[WARN] Aucun aéroport ou runway d'arrivée pour {flight.flight_code}")
        return False

    available = [r for r in arrival_airport.runways if r.can_schedule()]
    if not available:
        return False

    chosen = min(available, key=lambda r: len(r.scheduled_flights))
    flight.arrival_runway_code = chosen.id
    flight.runway_usage = RunwayUsageType.ARRIVAL

    chosen.add_flight(flight)
    chosen.scheduled_flights.sort(
        key=lambda f: f.estimated_arrival_time or datetime.max
    )

    return True
