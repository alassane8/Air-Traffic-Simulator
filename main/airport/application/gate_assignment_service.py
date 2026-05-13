import random

from airport.application.taxiway_pathfinding_service import find_path_graph, path_total_distance
from airport.domain.gate import Gate


def assign_aircrafts_to_gates(aircrafts: dict, gates: dict, terminals: dict) -> list:
    """Assigne aléatoirement des avions aux gates disponibles au démarrage du simulateur."""
    occupied_gates = []

    unassigned_aircraft_ids = set(aircrafts.keys())
    unassigned_gate_ids = set(gates.keys())

    while unassigned_aircraft_ids and unassigned_gate_ids:
        aircraft_id = random.choice(list(unassigned_aircraft_ids))
        gate_id = random.choice(list(unassigned_gate_ids))

        selected_aircraft = aircrafts[aircraft_id]
        selected_gate = gates[gate_id]
        terminal = terminals[selected_gate.terminal]

        unassigned_aircraft_ids.discard(aircraft_id)
        unassigned_gate_ids.discard(gate_id)

        if not terminal.can_accept_plane() or not terminal.is_open():
            continue

        terminal.add_plane()
        selected_gate.assign_aircraft(selected_aircraft.id)
        occupied_gates.append(selected_gate)

    return occupied_gates


def find_best_landing_gate(
    arrival_airport,
    runways: dict,
    nodes: dict,
    edges: dict,
    terminals: dict,
    flight,
) -> Gate | None:
    """Trouve la gate d'arrivée la plus proche (distance taxiway minimale)."""
    if arrival_airport is None:
        return None

    available_gates = {gate.id: gate for gate in arrival_airport.gates if gate.is_free()}
    ref_to_node_id = {node.ref: node.id for node in nodes.values()}

    if not flight.arrival_runway_code:
        return None

    runway = runways.get(flight.arrival_runway_code)
    if not runway:
        print(f"[WARN] Runway d'arrivée '{flight.arrival_runway_code}' introuvable pour {flight.flight_code}")
        return None

    start_id = ref_to_node_id.get(runway.id)
    if not start_id:
        return None

    best_gate = None
    best_distance = float("inf")

    for gate in available_gates.values():
        terminal = terminals.get(gate.terminal)
        if terminal is None:
            continue
        if not terminal.can_accept_plane() or not terminal.is_open():
            continue

        goal_id = ref_to_node_id.get(gate.id)
        if not goal_id:
            continue

        path = find_path_graph(nodes, edges, start_id, goal_id)
        if not path:
            continue

        distance = path_total_distance(path, nodes, edges)
        if distance < best_distance:
            best_distance = distance
            best_gate = gate

    return best_gate
