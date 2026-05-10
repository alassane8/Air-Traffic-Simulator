import time

from shared import data_loader, init_logger, object_factory, simulator
from airport.application.gate_assignment_service import assign_aircrafts_to_gates


def init_simulator_data():
    init_logger.log(">>> BOOT SEQUENCE INITIATED...")
    time.sleep(0.8)

    init_logger.phase("Loading data modules")

    init_logger.loading("Fetching aeronautical data")
    aircrafts_data = data_loader.load_data("aircraft/aircrafts.json")
    init_logger.success("Aircraft data loaded")

    init_logger.loading("Fetching airport infrastructure")
    airports_data = data_loader.load_data("airport/airports.json")
    init_logger.success("Airport data loaded")

    init_logger.loading("Fetching air corridor data")
    air_corridors_data = data_loader.load_data("air_corridor/air_corridors.json")
    init_logger.success("Air corridor data loaded")

    init_logger.loading("Fetching airlines data")
    airlines_data = data_loader.load_data("airline/airlines.json")
    init_logger.success("Airline data loaded")

    init_logger.phase("Building system objects")

    init_logger.loading("Assembling aerial units")
    aircrafts = object_factory.create_aircrafts(aircrafts_data)
    init_logger.success(f"{len(aircrafts)} aircraft operational")

    init_logger.loading("Initializing airport hubs")
    airports = object_factory.create_airports(airports_data)
    init_logger.success(f"{len(airports)} airports online")

    init_logger.loading("Defining air corridors")
    air_corridors = object_factory.create_air_corridors(air_corridors_data)
    init_logger.success(f"{len(air_corridors)} air corridors operational")

    init_logger.loading("Deploying terminals")
    terminals = object_factory.create_terminals(airports_data)
    init_logger.success(f"{len(terminals)} terminals active")

    init_logger.loading("Instanciating airlines")
    airlines = object_factory.create_airlines(airlines_data)
    init_logger.success(f"{len(airlines)} airlines active")

    init_logger.loading("Activating boarding gates")
    gates = object_factory.create_gates(airports_data)
    init_logger.success(f"{len(gates)} gates ready")

    init_logger.loading("Synchronizing runways")
    runways = object_factory.create_runways(airports_data)
    init_logger.success(f"{len(runways)} runways operational")

    init_logger.loading("Indexing taxiway nodes")
    nodes = object_factory.create_nodes(airports_data)
    init_logger.success(f"{len(nodes)} nodes indexed")

    init_logger.loading("Connecting taxiway edges")
    edges = object_factory.create_edges(airports_data)
    init_logger.success(f"{len(edges)} edges connected")

    init_logger.loading("Plotting waypoints")
    waypoints = object_factory.create_waypoints(air_corridors_data)
    init_logger.success(f"{len(waypoints)} waypoints plotted")

    init_logger.phase("System ready")
    init_logger.log(">>> ALL SYSTEMS NOMINAL")
    time.sleep(0.5)
    init_logger.log(">>> READY FOR DEPLOYMENT")

    object_factory.update_airports_with_terminals(airports, terminals)
    object_factory.update_airports_with_gates(airports, gates)
    object_factory.update_airports_with_runways(airports, runways)

    occupied_gates = assign_aircrafts_to_gates(aircrafts, gates, terminals)

    simulator.run_simulation(
        terminals, waypoints, aircrafts, airports,
        air_corridors, airlines, runways, occupied_gates,
        edges, nodes, gates,
    )
