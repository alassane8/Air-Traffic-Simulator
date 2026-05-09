from datetime import datetime
import random
from gate import GateStatus
from terminal import TerminalStatus

def assign_aircrafts_to_gates(aircrafts: dict, gates: dict, terminals: dict) -> list:
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
            continue  # gate et avion perdus, mais au moins la boucle s'arrête proprement

        if selected_aircraft.has_capacity():
            selected_aircraft.load_passengers(random.randrange(selected_aircraft.seats))

        terminal.add_plane()
        selected_gate.assign_aircraft(selected_aircraft.id)
        occupied_gates.append(selected_gate)

    return occupied_gates