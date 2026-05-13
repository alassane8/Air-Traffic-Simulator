from datetime import datetime, timedelta

from flight.domain.flight import Flight, FlightStatus, FlightPriority, RunwayUsageType


# ── STATUS ────────────────────────────────────────────────────────────────────

def is_in_air(flight: Flight) -> bool:
    return flight.flight_status in (
        FlightStatus.TAKEOFF,
        FlightStatus.CLIMBING,
        FlightStatus.CRUISE,
        FlightStatus.DESCENDING,
    )

def is_on_ground(flight: Flight) -> bool:
    return flight.flight_status in (
        FlightStatus.PLANNED,
        FlightStatus.LINEUP,
        FlightStatus.LANDING,
        FlightStatus.TAXI,
        FlightStatus.PARKED,
    )

def is_departing(flight: Flight) -> bool:
    return flight.runway_usage == RunwayUsageType.DEPARTURE

def is_arriving(flight: Flight) -> bool:
    return flight.runway_usage == RunwayUsageType.ARRIVAL

def is_completed(flight: Flight) -> bool:
    return flight.flight_status == FlightStatus.PARKED

def is_active(flight: Flight) -> bool:
    return not is_completed(flight) and flight.flight_status != FlightStatus.PLANNED


# ── PRIORITY ──────────────────────────────────────────────────────────────────

def is_emergency(flight: Flight) -> bool:
    return flight.priority == FlightPriority.EMERGENCY

def is_critical(flight: Flight) -> bool:
    return flight.priority in (
        FlightPriority.EMERGENCY,
        FlightPriority.FUEL_CRITICAL,
        FlightPriority.MEDICAL,
    )

def compare_priority(flight_a: Flight, flight_b: Flight) -> int:
    """Retourne négatif si flight_a a une priorité plus haute, positif sinon, 0 si égal."""
    return flight_a.priority.order - flight_b.priority.order

def sort_by_priority(flights: list[Flight]) -> list[Flight]:
    return sorted(flights, key=lambda f: f.priority.order)


# ── TRANSITIONS ───────────────────────────────────────────────────────────────

DEPARTURE_SEQUENCE = [
    FlightStatus.PLANNED,
    FlightStatus.LINEUP,
    FlightStatus.TAKEOFF,
    FlightStatus.CLIMBING,
    FlightStatus.CRUISE,
    FlightStatus.DESCENDING,
    FlightStatus.LANDING,
    FlightStatus.TAXI,
    FlightStatus.PARKED,
]

def advance_status(flight: Flight) -> bool:
    """Passe le vol au statut suivant. Retourne False si déjà au statut final."""
    try:
        current_index = DEPARTURE_SEQUENCE.index(flight.flight_status)
        if current_index < len(DEPARTURE_SEQUENCE) - 1:
            flight.flight_status = DEPARTURE_SEQUENCE[current_index + 1]
            flight.updated_at = datetime.now()
            return True
        return False
    except ValueError:
        return False

def set_status(flight: Flight, status: FlightStatus) -> None:
    flight.flight_status = status
    flight.updated_at = datetime.now()


# ── TIME ──────────────────────────────────────────────────────────────────────

def is_delayed(flight: Flight) -> bool:
    if flight.flight_status == FlightStatus.PARKED:
        return flight.arrival_time > flight.estimated_arrival_time
    return datetime.now() > flight.estimated_departure_time and flight.flight_status == FlightStatus.PLANNED

def get_flight_duration(flight: Flight) -> float | None:
    """Retourne la durée réelle du vol en minutes, ou None si non terminé."""
    if flight.departure_time and flight.arrival_time:
        delta = flight.arrival_time - flight.departure_time
        return delta.total_seconds() / 60
    return None

def get_estimated_duration(flight: Flight) -> timedelta | None:
    if flight.estimated_departure_time and flight.estimated_arrival_time:
        return flight.estimated_arrival_time - flight.estimated_departure_time
    return None

def get_delay_minutes(flight: Flight) -> float:
    """Retourne le retard en minutes (positif = en retard, négatif = en avance)."""
    if flight.flight_status == FlightStatus.PARKED:
        return (flight.arrival_time - flight.estimated_arrival_time).total_seconds() / 60
    return (datetime.now() - flight.estimated_departure_time).total_seconds() / 60


# ── DISPLAY ───────────────────────────────────────────────────────────────────

def format_flight(flight: Flight) -> str:
    return (
        f"[{flight.flight_code}] "
        f"{flight.depart_airport_id} → {flight.arrival_airport_code} | "
        f"Status: {flight.flight_status.label} | "
        f"Priority: {flight.priority.label}"
    )
