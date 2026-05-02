from datetime import datetime
import random
from aircraft import AircraftType
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

        if selected_aircraft.seats > 0:
            selected_aircraft.passengers = random.randrange(selected_aircraft.seats)
        else: 
            selected_aircraft.passengers = 0

        selected_aircraft.updated_at = datetime.now
        
        selected_gate = random.choice(list(remaining_gates.values()))

        while selected_gate.status == GateStatus.OCCUPIED:
            selected_gate = random.choice(list(remaining_gates.values()))

        selected_gate.status = GateStatus.OCCUPIED
        selected_gate.aircraft_id = selected_aircraft.id
        selected_gate.updated_at = datetime.now
        occupied_gates.append(selected_gate)

        terminal_to_update = terminals[selected_gate.terminal]

        if terminal_to_update.planes_on_deck < terminal_to_update.max_planes and terminal_to_update.status == TerminalStatus.OPEN :
            terminal_to_update.planes_on_deck += 1 
            terminal_to_update.updated_at = datetime.now

        print(f"Aircraft {selected_aircraft.id} with {selected_aircraft.passengers} on board placed in {selected_gate.id} ready for takeoff")

        del remaining_gates[selected_gate.id]
        del remaining_aircrafts[selected_aircraft.id]

    return occupied_gates