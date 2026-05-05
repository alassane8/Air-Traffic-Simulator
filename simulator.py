from datetime import datetime
import random
from gate import GateStatus
from terminal import TerminalStatus

def assign_aircrafts_to_gates(aircrafts: dict, gates: dict, terminals: dict) -> list:
    """
    Placement aleatoire des avions dans les portes des aeroports
    """
    unassigned_aircraft_ids = set(aircrafts.keys())
    unassigned_gate_ids = set(gates.keys())
    occupied_gates = []

    while unassigned_aircraft_ids:
        aircraft_id = random.choice(list(unassigned_aircraft_ids))
        gate_id = random.choice(list(unassigned_gate_ids))

        selected_aircraft = aircrafts[aircraft_id]
        selected_gate = gates[gate_id]

        if selected_aircraft.has_capacity():
            selected_aircraft.load_passengers(random.randrange(selected_aircraft.seats))
        else:
            selected_aircraft.load_passengers(0)

        selected_gate.assign_aircraft(selected_aircraft.id)
        occupied_gates.append(selected_gate)

        terminal = terminals[selected_gate.terminal]
        if terminal.can_accept_plane() and terminal.is_open():
            terminal.add_plane()

        print(f"Aircraft {selected_aircraft.id} with {selected_aircraft.passengers} on board placed in {selected_gate.id} {selected_gate.terminal} ready for takeoff")

        unassigned_aircraft_ids.discard(aircraft_id)
        unassigned_gate_ids.discard(gate_id)

    return occupied_gates