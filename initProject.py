import time

import createObjects
import initLogs
import loadData
from scheduler import flight_scheduler
import simulator


def initSimulatorData():
    
    initLogs.log(">>> BOOT SEQUENCE INITIATED...")
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

    initLogs.loading("Indexing taxiway nodes")
    nodes = createObjects.createNodes(airportsData)
    initLogs.success(f"{len(nodes)} nodes indexed")

    initLogs.loading("Connecting taxiway edges")
    edges = createObjects.createEdges(airportsData)
    initLogs.success(f"{len(edges)} edges connected")

    initLogs.loading("Plotting waypoints")
    waypoints = createObjects.createWaypoints(airCorridorsData)
    initLogs.success(f"{len(waypoints)} waypoints plotted")

    initLogs.phase("System ready")

    initLogs.log(">>> ALL SYSTEMS NOMINAL")
    time.sleep(0.5)
    initLogs.log(">>> READY FOR DEPLOYMENT")

    gates_to_initialize = gates.copy()
    aircrafts_to_initialize = aircrafts.copy()
    terminals_to_initialize = terminals.copy()

    occupied_gates = simulator.initializeAircraftsPositions(aircrafts_to_initialize, gates_to_initialize, terminals_to_initialize)

    createObjects.updateAirportsWithTerminals(airports, terminals)
    createObjects.updateAirportsWithGates(airports, gates)
    createObjects.updateAirportsWithRunways(airports, runways)

    flight_scheduler.schedule_flights(terminals, aircrafts, airlines, runways, occupied_gates)

    flight_scheduler.scheduler(runways, airports, aircrafts, airCorridors)

    initLogs.log_runways(runways)