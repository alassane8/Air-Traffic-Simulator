from air_corridor.domain.air_corridor import AirCorridor


def find_corridor_for_departure(
    air_corridors: dict,
    departure_terminal_id: str,
    airports: dict,
    aircraft,
) -> AirCorridor | None:
    """
    Trouve un corridor disponible depuis l'aéroport du terminal de départ.
    """
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

    for corridor in air_corridors.values():
        is_available = corridor.has_capacity()
        is_correct_departure = corridor.from_airport == departure_airport.id
        is_open = corridor.is_open()
        is_direction_ok = corridor.is_direction_allowed(
            corridor.from_airport, corridor.to_airport
        )

        if is_available and is_correct_departure and is_open and is_direction_ok:
            if aircraft not in corridor.aircrafts:
                corridor.aircrafts.append(aircraft)
            return corridor

    print(f"[ERROR] Aucun corridor disponible depuis l'aéroport {departure_airport.id}")
    return None
