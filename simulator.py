import random
from gate import GateStatus

def initializeAircraftsPositions(aircrafts, gates):
    """"
    Placement aleatoire des avions dans les portes des aeroports
    """
    remaining_aircrafts = aircrafts
    remaining_gates = gates
    
    while remaining_aircrafts:
        selected_aircraft = random.choice(list(remaining_aircrafts.values()))
        selected_aircraft.passengers = random.randrange(selected_aircraft.seats)
        selected_gate = random.choice(list(remaining_gates.values()))

        while selected_gate.status == GateStatus.OCCUPIED:
            selected_gate = random.choice(list(remaining_gates.values()))

        selected_gate.status = GateStatus.OCCUPIED
        selected_gate.aircraft_id = selected_aircraft.id

        print(f"Aircraft {selected_aircraft.id} with {selected_aircraft.passengers} on board placed in {selected_gate.id} ready for takeoff")

        del remaining_gates[selected_gate.id]
        del remaining_aircrafts[selected_aircraft.id]
