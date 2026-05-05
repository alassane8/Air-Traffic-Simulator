import random
import uuid

from airline import Airline
from flight import Flight, FlightPriority, FlightStatus, RunwayUsageType
from gate import Gate


def creatingFlight(airline: Airline, gate: Gate, terminals: dict, choosed_runway_id: str) -> Flight:

        return Flight(
            id=uuid.uuid4(),
            flight_code=initFlightCode(airline),
            flight_status=FlightStatus.PLANNED,
            airline_id=airline.id,
            aircraft_code=gate.aircraft_id,
            priority=initFlightPriority(),
            depart_airport_code=terminals[gate.terminal].airport_id,
            depart_terminal_code=gate.terminal,
            depart_gate_code=gate.id,
            depart_runway_code=choosed_runway_id,
            corridor_code=None,
            arrival_airport_code=None,
            arrival_terminal_code=None,
            arrival_gate_code=None,
            arrival_runway_code=None,
            runway_usage=RunwayUsageType.DEPARTURE,
            estimated_departure_time=None,
            estimated_arrival_time=None,
            departure_time=None,
            arrival_time=None,
        )   

def initFlightCode(airline: list) -> str:
    flight_number = random.randint(100, 1000)
    return f"{airline.iata_code}{flight_number}"

def initFlightPriority() -> FlightPriority:
    return random.choices([
                    FlightPriority.EMERGENCY, 
                    FlightPriority.FUEL_CRITICAL,
                    FlightPriority.MEDICAL, 
                    FlightPriority.DELAY, 
                    FlightPriority.NORMAL
                    ], weights=[1, 2, 3, 10, 84])[0]