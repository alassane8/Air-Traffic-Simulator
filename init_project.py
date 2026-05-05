import time
import create_objects
import init_logs
import load_data
from scheduler import schedule
import simulator


def init_simulator_data():
    
    init_logs.log(">>> BOOT SEQUENCE INITIATED...")
    time.sleep(0.8)

    init_logs.phase("Loading data modules")

    init_logs.loading("Fetching aeronautical data")
    aircraftsData = load_data.load_data('aircrafts.json')
    init_logs.success("Aircraft data loaded")

    init_logs.loading("Fetching airport infrastructure")
    airportsData = load_data.load_data('airports.json')
    init_logs.success("Airport data loaded")

    init_logs.loading("Fetching air corridor data")
    airCorridorsData = load_data.load_data('air_corridors.json')
    init_logs.success("Air corridor data loaded")

    init_logs.loading("Fetching airlines data")
    airlinesData = load_data.load_data('airlines.json')
    init_logs.success("Airline data loaded")

    init_logs.phase("Building system objects")

    init_logs.loading("Assembling aerial units")
    aircrafts = create_objects.create_aircrafts(aircraftsData)
    init_logs.success(f"{len(aircrafts)} aircraft operational")

    init_logs.loading("Initializing airport hubs")
    airports = create_objects.create_airports(airportsData)
    init_logs.success(f"{len(airports)} airports online")

    init_logs.loading("Defining air corridors")
    airCorridors = create_objects.create_air_corridors(airCorridorsData)
    init_logs.success(f"{len(airCorridors)} air corridors operational")

    init_logs.loading("Deploying terminals")
    terminals = create_objects.create_terminals(airportsData)
    init_logs.success(f"{len(terminals)} terminals active")

    init_logs.loading("Instanciating airlines")
    airlines = create_objects.create_airlines(airlinesData)
    init_logs.success(f"{len(airlines)} airlines active")

    init_logs.loading("Activating boarding gates")
    gates = create_objects.create_gates(airportsData)
    init_logs.success(f"{len(gates)} gates ready")

    init_logs.loading("Synchronizing runways")
    runways = create_objects.create_runways(airportsData)
    init_logs.success(f"{len(runways)} runways operational")

    init_logs.loading("Indexing taxiway nodes")
    nodes = create_objects.create_nodes(airportsData)
    init_logs.success(f"{len(nodes)} nodes indexed")

    init_logs.loading("Connecting taxiway edges")
    edges = create_objects.create_edges(airportsData)
    init_logs.success(f"{len(edges)} edges connected")

    init_logs.loading("Plotting waypoints")
    waypoints = create_objects.create_waypoints(airCorridorsData)
    init_logs.success(f"{len(waypoints)} waypoints plotted")

    init_logs.phase("System ready")

    init_logs.log(">>> ALL SYSTEMS NOMINAL")
    time.sleep(0.5)
    init_logs.log(">>> READY FOR DEPLOYMENT")
    
    create_objects.update_airports_with_terminals(airports, terminals)
    create_objects.update_airports_with_gates(airports, gates)
    create_objects.update_airports_with_runways(airports, runways)

    occupied_gates = simulator.assign_aircrafts_to_gates(aircrafts, gates, terminals)

    schedule.simulation(terminals, aircrafts, airports, airCorridors, airlines, runways, occupied_gates, edges, nodes, gates)

