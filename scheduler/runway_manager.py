from datetime import datetime
import random

from aircraft import AircraftType
from flight import Flight, FlightStatus, RunwayUsageType
from flight_helpers import isDeparting, sortByPriority
from scheduler.corridor_manager import initCorridor
from scheduler.flight_timing import initFlightEstimatedDepartureTime
from scheduler.fligth_factory import creatingFlight


# ── HELPERS INTERNES ──────────────────────────────────────────────────────────

def _find_aircraft(gate, aircrafts: dict):
    """
    Retrouve l'objet Aircraft associé à une gate.

    Au boot, gate.aircraft_id contient l'UUID de l'avion (clé du dict aircrafts).
    Après un atterrissage, schedule.py appelle gate.assign_aircraft(flight.aircraft_code),
    qui stocke le CODE (ex: "B737") et non l'UUID → la recherche directe échoue.
    Ce helper essaie d'abord par id, puis par aircraft_code en fallback.
    """
    if gate.aircraft_id is None:
        return None

    # Recherche principale : gate.aircraft_id == clé du dict (UUID)
    aircraft = aircrafts.get(gate.aircraft_id)
    if aircraft is not None:
        return aircraft

    # Fallback : gate.aircraft_id contient le aircraft_code (après atterrissage)
    for a in aircrafts.values():
        if a.aircraft_code == gate.aircraft_id or a.id == gate.aircraft_id:
            return a

    return None


# ── DÉPART ───────────────────────────────────────────────────────────────────

def assign_flight_to_departure_runway(
    terminals: dict, aircrafts: dict, airlines: dict, runways: dict,
    occupied_gates: list, airports: dict, airCorridors: dict, existing_departures=None
) -> dict:
    """
    Crée les vols de départ, les assigne à une runway de départ,
    et initialise le corridor + aéroport d'arrivée.
    La runway d'arrivée sera choisie pendant le cruise.
    """
    existing_departures = existing_departures or {}
    departure_flights = {}

    # Gates déjà associées à un vol actif
    gates_already_assigned = {
        f.depart_gate_code for f in existing_departures.values()
    }
    occupied_gates[:] = [g for g in occupied_gates if g.is_occupied() and g.aircraft_id is not None]


    for gate in occupied_gates:
        if gate.id in gates_already_assigned:
            continue

        terminal = terminals.get(gate.terminal)
        if terminal is None:
            print(f"[WARN] Terminal '{gate.terminal}' introuvable pour gate {gate.id}, ignoré")
            continue

        airport_id = terminal.airport_id

        # ── FIX : recherche robuste de l'aircraft (UUID ou aircraft_code) ──
        aircraft = _find_aircraft(gate, aircrafts)
        if aircraft is None:
            print(f"[WARN] Aircraft introuvable pour gate {gate.id} "
                  f"(aircraft_id={gate.aircraft_id!r}), vol ignoré")
            continue

        airline = random.choice(list(airlines.values()))
        aircraft_type = aircraft.aircraft_type

        airport_runways = {
            runway.id: runway
            for runway in runways.values()
            if runway.airport_id == airport_id
        }

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

        # On passe l'aircraft directement pour que flight.aircraft_code = aircraft.id (UUID stable)
        # et non gate.aircraft_id qui peut valoir None si la gate a déjà été libérée
        created_flight = creatingFlight(airline, gate, terminals, chosen_runway.id, aircraft)

        # Initialiser le corridor et la destination (sans runway d'arrivée)
        air_corridor = initCorridor(airCorridors, gate.terminal, airports, aircraft)
        if air_corridor is None:
            print(f"[WARN] Aucun corridor pour le vol depuis {gate.id}")
            continue

        created_flight.corridor_code        = air_corridor.air_corridor_code
        created_flight.arrival_airport_code = air_corridor.to_airport
        created_flight.dest_lat             = _get_airport_lat(created_flight.arrival_airport_code, airports)
        created_flight.dest_lon             = _get_airport_lon(created_flight.arrival_airport_code, airports)
        created_flight.status               = FlightStatus.PLANNED

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