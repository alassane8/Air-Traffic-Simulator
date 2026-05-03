def sortFlightsByPriority(scheduled_flights: list) -> list:
    return sorted(scheduled_flights, key=lambda flight: flight.priority.order)

