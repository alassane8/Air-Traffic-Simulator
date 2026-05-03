""""

Création d'un dictionnaire qui répertorie dans l'ordre des départs les vols des avions en fonction de la priorités 
Dans chaque vol : 
    Génération d'un code de vol
    Assignation à un aéroport de destination parmis aéroport disponible (corridors existants, airports available, airport pas celui de depart)
    Définir une heure de départ en fonction de la priorité du vol et des paramaètres de l'avion "à déterminer"
    Déterminer heure d'arrivée en fonction de la vitesse de croisière de l'avion et des phases du vol
    Phases du vol possède une durée: 
        - PLANNED: 1h
        - BOARDING: 1h 
        - LINEUP: 10m
        - TAKEOFF: 3m
        - CLIMBING: 20m
        - CRUISING: à calculer 
        - DESCENDING: 20m
        - LANDING: 3m
        - PARKED: 10m
        La somme de tous ces valeurs est la différence entre heure de départ et heure d'arrivée prévu

Une piste est choisie pour un avion en fonction de sa taille Plus l'avion est grand plus la piste doit être longue.     
Pour chaque runway, le scheduler créer une liste de vol. La liste est trié par ordre de départ et de proriter du vol 
Le premier vol de la liste est envoyé sur la piste il doit avoir le statue lineup.

Création d'un vol statut planned
Association à une piste boarding
Comparaison priorité des vol pour voir ou l'avion se situe dans liste runway Lineup
    si normal = dernier des normal 
    si emergency = dernier des emergency etc etc

définition heure de départ 5 min après dernier vol de la prioriter => estimated arrival time calculated
definir temps de vol pour chaque vol
definir heure d'arrivee
Association à la liste runway arrival en fonction du arrival time: 
    taille de la piste en fonction de taille avion 
    trier par heure d'arriver sur runway
    prioriter du vol 
    heure d'arriver

avion en haut de la liste décolle/attéris => apparait en bas liste arrival runway de aeroport d'arrivé
ou vont les avions une fois décoller et supprimer de la liste ? historique de vol qui log tous le parcours de l'avion. 
( Une liste par runway par aeroport ) 

"""
from datetime import datetime
import random
import uuid
from aircraft import Aircraft, AircraftType
from airline import Airline
from gate import Gate
from airCorridor import AirCorridor, CorridorDirection, CorridorStatus
from runway import Runway
from flight import Flight, FlightStatus, FlightPriority
from terminal import Terminal

def schedule_flights(
        terminals: dict, 
        aircrafts: dict,
        airlines: dict,
        runways: dict,
        occupied_gates: list):

    for gate in occupied_gates:
        terminal = terminals[gate.terminal]
        airport_id = terminal.airport_id
        airport_runways = {}
        aircraft = aircrafts.get(gate.aircraft_id)
        airline = random.choice(list(airlines.values()))
        aircraft_type = aircraft.aircraft_type

        for runway in runways.values():
            if runway.airport_id == airport_id:
                airport_runways[runway.id] = runway

        shortest_runway = min(airport_runways.values(), key=lambda runway: runway.length)
        longest_runway = max(airport_runways.values(), key=lambda runway: runway.length)

        if aircraft_type == AircraftType.NARROW:
            choosed_runway = random.choice(list(airport_runways.values()))
            
        elif aircraft_type == AircraftType.LARGE:
            eligible = [r for r in airport_runways.values() if r.id != shortest_runway.id]
            choosed_runway = random.choice(eligible)
            
        else:
            choosed_runway = longest_runway

        choosed_runway_id = choosed_runway.id
        created_Flight = creatingFlight(airline, gate, terminals, choosed_runway_id)
        choosed_runway.scheduled_flights.append(created_Flight)


    for runway in runways.values():
        print(" ")
        print(" ")
        print(f"Runway {runway.id}   : {runway.scheduled_flights}")
        print(" ")
        print(" ")

    """
    trier par ordre de prioriter
    Comparaison priorité des vol pour voir ou l'avion se situe dans liste runway Lineup
    si normal = dernier des normal 
    si emergency = dernier des emergency etc etc
    """
        # created_Flight.estimated_departure_time = 
        # created_Flight.estimated_arrival_time = 
        # created_Flight.departure_time = 
        # created_Flight.arrival_time = 
        # created_Flight.corridor_code = 
        # created_Flight.arrival_airport_code = 
        # created_Flight.arrival_terminal_code =
        # created_Flight.arrival_gate_code = 
        # created_Flight.arrival_gate_code = 

def creatingFlight(airline: Airline, gate: Gate, terminals: dict, choosed_runway_id: str) -> Flight:

        return Flight(
            id=uuid.uuid4(),
            flight_code=initFlightCode(airline),
            flight_status=FlightStatus.PLANNED,
            airline_id= airline.id,
            aircraft_code=gate.aircraft_id,
            priority=initFlightPriority(),
            estimated_departure_time=None,
            estimated_arrival_time=None,
            departure_time=None,
            arrival_time=None,
            depart_airport_code=terminals[gate.terminal].airport_id,
            depart_terminal_code=gate.terminal,
            depart_gate_code=gate.gate_code,
            depart_runway_code=choosed_runway_id,
            corridor_code=None,
            arrival_airport_code=None,
            arrival_terminal_code=None,
            arrival_gate_code=None,
            arrival_runway_code=None,
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

def initCorridor(airCorridors: dict, departure_terminal: Terminal, arrival_terminal: Terminal, aircraft: Aircraft) -> AirCorridor:

    for airCorridor in airCorridors.values():
        is_available = len(airCorridor.aircrafts) < airCorridor.max_capacity
        is_correct_route = (airCorridor.from_airport == departure_terminal.airport_id and 
                            airCorridor.to_airport == arrival_terminal.airport_id)
        is_open = airCorridor.status == CorridorStatus.OPEN
        is_bidirectional = airCorridor.direction == CorridorDirection.BIDIRECTIONAL

        if is_available and is_correct_route and is_open and is_bidirectional:
            airCorridor.aircrafts[aircraft.id] = aircraft
            print(airCorridor)
            return airCorridor

    return None



# def initGateArrival() -> Gate:
    
#     return None

# def initRunwayArrival() -> Runway:
#     return None

# def initFlightDepartureTime() -> datetime:
#     return None

# def initFlightArrivalTime() -> datetime:
#     return None