from datetime import datetime
import random
import uuid
from gate import Gate, GateStatus
from airCorridor import AirCorridor
from runway import Runway
from terminal import TerminalStatus
from flight import Flight, FlightStatus, FlightPriority

def initializeAircraftsPositions(aircrafts: dict, gates: dict, terminals: dict) -> list:
    """"
    Placement aleatoire des avions dans les portes des aeroports
    """
    remaining_aircrafts = aircrafts
    remaining_gates = gates
    occupied_gates = {}
    
    while remaining_aircrafts:
        selected_aircraft = random.choice(list(remaining_aircrafts.values()))

        selected_aircraft.passengers = random.randrange(selected_aircraft.seats)
        selected_aircraft.updated_at = datetime.now
        
        selected_gate = random.choice(list(remaining_gates.values()))

        while selected_gate.status == GateStatus.OCCUPIED:
            selected_gate = random.choice(list(remaining_gates.values()))

        selected_gate.status = GateStatus.OCCUPIED
        selected_gate.aircraft_id = selected_aircraft.id
        selected_gate.updated_at = datetime.now
        occupied_gates = list.append(selected_gate)

        terminal_to_update = terminals[selected_gate.terminal]

        if terminal_to_update.planes_on_deck < terminal_to_update.max_planes and terminal_to_update.status == TerminalStatus.OPEN :
            terminal_to_update.planes_on_deck += 1 
            terminal_to_update.updated_at = datetime.now

        print(f"Aircraft {selected_aircraft.id} with {selected_aircraft.passengers} on board placed in {selected_gate.id} ready for takeoff")

        del remaining_gates[selected_gate.id]
        del remaining_aircrafts[selected_aircraft.id]

        return occupied_gates


def flightInitialization(occupied_gates: list, terminals: dict):

    for gate in occupied_gates:
        new_flighzt = Flight(
            id=uuid.uuid4(),
            flight_code=initFlightCode(),
            flight_status=initFlightStatus(),
            aircraft_code=gate.aircraft_id,
            priority=initFlightPriority(),
            estimated_departure_time=initFlightDepartureTime(),
            estimated_arrival_time=initFlightArrivalTime(),
            departure_time=None,
            arrival_time=None,
            depart_airport_code=terminals[gate.terminal].airport_id,
            depart_terminal_code=gate.terminal,
            depart_gate_code=gate.gate_code,
            depart_runway_code=initRunwayDeparture().id,
            corridor_code=initCorridor().air_corridor_code,
            arrival_airport_code=terminals[initGateArrival().terminal].airport_id,
            arrival_terminal_code=terminals[initGateArrival().terminal].terminal_code,
            arrival_gate_code=initGateArrival().gate_code,
            arrival_runway_code=initRunwayArrival().id,
)

    # status planned, aircraft code, priority random avec + de proba sur normal
    # choisir estimated en random
def initFlightCode() -> str:


def initFlightStatus() -> FlightStatus:


def initFlightPriority() -> FlightPriority:


def initFlightDepartureTime() -> datetime:


def initFlightArrivalTime() -> datetime:


def initRunwayDeparture() -> Runway:


def initCorridor() -> AirCorridor:


def initGateArrival() -> Gate:


def initRunwayArrival() -> Runway: