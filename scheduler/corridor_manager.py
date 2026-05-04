
from airCorridor import AirCorridor, CorridorDirection, CorridorStatus
from aircraft import Aircraft


def initCorridor(airCorridors: dict, departure_terminal_id: str, airports: dict, aircraft: Aircraft) -> AirCorridor:
    departure_airport = None

    for airport in airports.values():
        for terminal in airport.terminals:
            if terminal.id == departure_terminal_id:
                departure_airport = airport
                break
        if departure_airport:
            break

    if not departure_airport:
        print(f"[ERROR] Aucun aéroport trouvé pour le terminal {departure_terminal_id}")
        return None

    for airCorridor in airCorridors.values():
        is_available = airCorridor.has_capacity()
        is_correct_departure_terminal = airCorridor.to_airport != departure_airport.id
        is_open = airCorridor.is_open()
        is_bidirectional = airCorridor.is_direction_allowed(airCorridor.from_airport, airCorridor.to_airport)

        if is_available and is_correct_departure_terminal and is_open and is_bidirectional:
            airCorridor.aircrafts.append(aircraft)
            return airCorridor

    print(f"[ERROR] Aucun corridor disponible depuis l'aéroport {departure_airport.id}")
    return None