import loadData
import createObjects
import initLogs 
import time
from scheduler import flight_scheduler
import simulator

def main() -> int:
    initLogs.log(">>> BOOT SEQUENCE INITIATED...", 0.04)
    time.sleep(0.8)

    initLogs.phase("Loading data modules")

    initLogs.loading("Fetching aeronautical data")
    aircraftsData = loadData.loadData('aircrafts.json')
    initLogs.success("Aircraft data loaded")

    initLogs.loading("Fetching airport infrastructure")
    airportsData = loadData.loadData('airports.json')
    initLogs.success("Airport data loaded")

    initLogs.loading("Fetching air corridor data")
    airCorridorsData = loadData.loadData('airCorridors.json')
    initLogs.success("Air corridor data loaded")

    initLogs.loading("Fetching airlines data")
    airlinesData = loadData.loadData('airlines.json')
    initLogs.success("Airline data loaded")

    initLogs.phase("Building system objects")

    initLogs.loading("Assembling aerial units")
    aircrafts = createObjects.createAircrafts(aircraftsData)
    initLogs.success(f"{len(aircrafts)} aircraft operational")

    initLogs.loading("Initializing airport hubs")
    airports = createObjects.createAirports(airportsData)
    initLogs.success(f"{len(airports)} airports online")

    initLogs.loading("Defining air corridors")
    airCorridors = createObjects.createAirCorridors(airCorridorsData)
    initLogs.success(f"{len(airCorridors)} air corridors operational")

    initLogs.loading("Deploying terminals")
    terminals = createObjects.createTerminals(airportsData)
    initLogs.success(f"{len(terminals)} terminals active")

    initLogs.loading("Instanciating airlines")
    airlines = createObjects.createAirlines(airlinesData)
    initLogs.success(f"{len(airlines)} airlines active")

    initLogs.loading("Activating boarding gates")
    gates = createObjects.createGates(airportsData)
    initLogs.success(f"{len(gates)} gates ready")

    initLogs.loading("Synchronizing runways")
    runways = createObjects.createRunways(airportsData)
    initLogs.success(f"{len(runways)} runways operational")

    initLogs.phase("System ready")

    initLogs.log(">>> ALL SYSTEMS NOMINAL", 0.04)
    time.sleep(0.5)
    initLogs.log(">>> READY FOR DEPLOYMENT", 0.04)

    gates_to_initialize = gates.copy()
    aircrafts_to_initialize = aircrafts.copy()
    terminals_to_initialize = terminals.copy()

    occupied_gates = simulator.initializeAircraftsPositions(aircrafts_to_initialize, gates_to_initialize, terminals_to_initialize)

    createObjects.updateAirportsWithTerminals(airports, terminals)
    createObjects.updateAirportsWithGates(airports, gates)
    createObjects.updateAirportsWithRunways(airports, runways)

    flight_scheduler.schedule_flights(terminals,aircrafts, airlines, runways, occupied_gates)
    
    flight_scheduler.scheduler(runways, airports, aircrafts, airCorridors)

    for runway in runways.values():
        print(f"\n{'='*60}")
        print(f"RUNWAY: {runway.id}")
        print(f"{'='*60}")
        
        if not runway.scheduled_flights:
            print("  Aucun vol schedulé")
            continue

        for flight in runway.scheduled_flights:
            print(f"\n  ✈ {flight.flight_code}")
            print(f"    Priorité        : {flight.priority.label}")
            print(f"    Usage Runway    : {flight.runway_usage.label}")
            print(f"    Départ airport  : {flight.depart_airport_code}")
            print(f"    Arrivée airport : {flight.arrival_airport_code}")
            print(f"    EST. départ     : {flight.estimated_departure_time}")
            print(f"    EST. arrivée    : {flight.estimated_arrival_time}")
            print(f"    Corridor        : {flight.corridor_code}")
            print(f"    {'─'*40}")

    total = sum(len(r.scheduled_flights) for r in runways.values())
    departures = sum(1 for r in runways.values() for f in r.scheduled_flights if f.runway_usage.value == "DEPARTURE")
    arrivals = sum(1 for r in runways.values() for f in r.scheduled_flights if f.runway_usage.value == "ARRIVAL")

    print(f"\nTotal entrées runways : {total}")
    print(f"Départs              : {departures}")
    print(f"Arrivées             : {arrivals}")

    return 0


if __name__ == '__main__':
    main()