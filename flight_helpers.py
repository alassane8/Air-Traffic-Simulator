from flight import Flight, FlightStatus, FlightPriority, RunwayUsageType
from datetime import datetime


# ── STATUS ──────────────────────────────────────────────────────────────────

def isInAir(flight: Flight) -> bool:
    return flight.flight_status in (
        FlightStatus.TAKEOFF,
        FlightStatus.CLIMBING,
        FlightStatus.CRUISE,
        FlightStatus.DESCENDING,
    )

def isOnGround(flight: Flight) -> bool:
    return flight.flight_status in (
        FlightStatus.PLANNED,
        FlightStatus.LINEUP,
        FlightStatus.LANDING,
        FlightStatus.PARKED,
    )

def isDeparting(flight: Flight) -> bool:
    return flight.runway_usage == RunwayUsageType.DEPARTURE

def isArriving(flight: Flight) -> bool:
    return flight.runway_usage == RunwayUsageType.ARRIVAL

def isCompleted(flight: Flight) -> bool:
    return flight.flight_status == FlightStatus.PARKED

def isActive(flight: Flight) -> bool:
    return not isCompleted(flight) and flight.flight_status != FlightStatus.PLANNED


# ── PRIORITY ─────────────────────────────────────────────────────────────────

def isEmergency(flight: Flight) -> bool:
    return flight.priority == FlightPriority.EMERGENCY

def isCritical(flight: Flight) -> bool:
    return flight.priority in (FlightPriority.EMERGENCY, FlightPriority.FUEL_CRITICAL, FlightPriority.MEDICAL)

def comparePriority(flightA: Flight, flightB: Flight) -> int:
    """Returns negative if flightA has higher priority, positive if lower, 0 if equal."""
    return flightA.priority.order - flightB.priority.order

def sortByPriority(flights: list[Flight]) -> list[Flight]:
    return sorted(flights, key=lambda f: f.priority.order)


# ── TRANSITIONS ──────────────────────────────────────────────────────────────

DEPARTURE_SEQUENCE = [
    FlightStatus.PLANNED,
    FlightStatus.LINEUP,
    FlightStatus.TAKEOFF,
    FlightStatus.CLIMBING,
    FlightStatus.CRUISE,
    FlightStatus.DESCENDING,
    FlightStatus.LANDING,
    FlightStatus.PARKED,
]

def advanceStatus(flight: Flight) -> bool:
    """Moves the flight to the next status. Returns False if already at final status."""
    try:
        current_index = DEPARTURE_SEQUENCE.index(flight.flight_status)
        if current_index < len(DEPARTURE_SEQUENCE) - 1:
            flight.flight_status = DEPARTURE_SEQUENCE[current_index + 1]
            flight.updated_at = datetime.now()
            return True
        return False
    except ValueError:
        return False

def setStatus(flight: Flight, status: FlightStatus) -> None:
    flight.flight_status = status
    flight.updated_at = datetime.now()


# ── TIME ─────────────────────────────────────────────────────────────────────

def isDelayed(flight: Flight) -> bool:
    if flight.flight_status == FlightStatus.PARKED:
        return flight.arrival_time > flight.estimated_arrival_time
    return datetime.now() > flight.estimated_departure_time and flight.flight_status == FlightStatus.PLANNED

def getFlightDuration(flight: Flight) -> float | None:
    """Returns actual flight duration in minutes, or None if not yet completed."""
    if flight.departure_time and flight.arrival_time:
        delta = flight.arrival_time - flight.departure_time
        return delta.total_seconds() / 60
    return None

def getEstimatedDuration(flight: Flight) -> float | None:
    """Returns estimated flight duration in minutes."""
    if flight.estimated_departure_time and flight.estimated_arrival_time:
        delta = flight.estimated_arrival_time - flight.estimated_departure_time
        return delta.total_seconds() / 60
    return None

def getDelayMinutes(flight: Flight) -> float:
    """Returns delay in minutes (positive = late, negative = early)."""
    if flight.flight_status == FlightStatus.PARKED:
        return (flight.arrival_time - flight.estimated_arrival_time).total_seconds() / 60
    return (datetime.now() - flight.estimated_departure_time).total_seconds() / 60


# ── DISPLAY ──────────────────────────────────────────────────────────────────

def formatFlight(flight: Flight) -> str:
    return (
        f"[{flight.flight_code}] "
        f"{flight.depart_airport_code} → {flight.arrival_airport_code} | "
        f"Status: {flight.flight_status.label} | "
        f"Priority: {flight.priority.label}"
    )