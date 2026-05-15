import random
from air_corridor.domain.air_corridor import AirCorridor
from air_corridor.domain.air_corridor_direction import CorridorDirection


def find_corridor_for_departure(
    air_corridors: dict,
    departure_terminal_id: str,
    airports: dict,
    aircraft,
) -> AirCorridor | None:
    """
    Trouve un corridor disponible depuis l'aéroport du terminal de départ.
    - Supporte les corridors BIDIRECTIONAL.
    - Choisit aléatoirement parmi les destinations disponibles (pas juste
      le premier corridor dans le dict), puis parmi les FL de cette destination.
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

    # Regrouper les corridors valides par destination
    # clé = airport_id destination, valeur = liste de corridors
    by_destination: dict[str, list] = {}

    for corridor in air_corridors.values():
        if not corridor.has_capacity() or not corridor.is_open():
            continue

        departs_forward = corridor.from_airport == departure_airport.id
        departs_reverse = (
            corridor.direction == CorridorDirection.BIDIRECTIONAL
            and corridor.to_airport == departure_airport.id
        )

        if not (departs_forward or departs_reverse):
            continue

        # Déterminer la destination réelle
        dest = corridor.to_airport if departs_forward else corridor.from_airport

        # Ne pas proposer un aller-retour vers soi-même
        if dest == departure_airport.id:
            continue

        by_destination.setdefault(dest, []).append(corridor)

    if not by_destination:
        print(f"[ERROR] Aucun corridor disponible depuis l'aéroport {departure_airport.id}")
        return None

    # 1. Choisir une destination au hasard (poids égaux)
    dest_chosen = random.choice(list(by_destination.keys()))

    # 2. Parmi les FL disponibles pour cette destination, choisir au hasard
    corridor = random.choice(by_destination[dest_chosen])

    if aircraft not in corridor.aircrafts:
        corridor.aircrafts.append(aircraft)

    return corridor