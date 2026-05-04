from datetime import datetime
import random
from gate import GateStatus
from terminal import TerminalStatus

def initializeAircraftsPositions(aircrafts: dict, gates: dict, terminals: dict) -> list:
    """"
    Placement aleatoire des avions dans les portes des aeroports
    """
    remaining_aircrafts = aircrafts
    remaining_gates = gates
    occupied_gates = []
    
    while remaining_aircrafts:
        selected_aircraft = random.choice(list(remaining_aircrafts.values()))

        if selected_aircraft.has_capacity():
            selected_aircraft.load_passengers(random.randrange(selected_aircraft.seats))
        else: 
            selected_aircraft.load_passengers(0)
        
        selected_gate = random.choice(list(remaining_gates.values()))

        while selected_gate.is_occupied():
            selected_gate = random.choice(list(remaining_gates.values()))

        selected_gate.assign_aircraft(selected_aircraft.id)
        occupied_gates.append(selected_gate)

        terminal_to_update = terminals[selected_gate.terminal]

        if terminal_to_update.can_accept_plane() and terminal_to_update.is_open() :
            terminal_to_update.add_plane()

        print(f"Aircraft {selected_aircraft.id} with {selected_aircraft.passengers} on board placed in {selected_gate.id} {selected_gate.terminal} ready for takeoff")

        del remaining_gates[selected_gate.id]
        del remaining_aircrafts[selected_aircraft.id]

    return occupied_gates