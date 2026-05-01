import loadData
import createObjects
import initLogs 
import time
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

    simulator.initializeAircraftsPositions(aircrafts, gates, terminals)

    return 0


if __name__ == '__main__':
    main()