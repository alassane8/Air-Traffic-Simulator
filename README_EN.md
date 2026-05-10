# AeroSim

AeroSim is an air traffic simulator written in Python, designed to realistically model the full lifecycle of a flight — from gate assignment to landing and return to stand. The project follows a **hexagonal architecture** (Ports & Adapters), with a clear separation between domain, business logic, and infrastructure.

---

## Project Assumptions

The simulator is built on several design assumptions made to keep complexity manageable in this first version:

- **One aircraft = one flight at a time.** An aircraft is assigned to a gate, generates a flight, takes off, lands, and becomes available again. Multi-leg rotations are not modelled.
- **JSON files are the single source of truth.** All airports, aircraft, airlines, and corridors are statically defined in configuration files. There is no database.
- **Time is accelerated via a `TIME_SCALE` factor.** One simulation tick corresponds to `TICK_INTERVAL * TIME_SCALE` simulated seconds. By default, `TIME_SCALE = 60`, meaning one real second equals one simulated minute.
- **Flight physics are simplified.** The geographical position is interpolated using the Haversine formula along a great circle. There is no simulation of aerodynamic forces, wind, or turbulence.
- **Corridors are bidirectional by default.** A corridor can be traversed in both directions unless specified otherwise in the configuration.
- **Flight priority is drawn randomly** from a weighted distribution (84% `NORMAL`, 10% `DELAY`, etc.), reflecting the statistical reality of air traffic.

---

## Configuration Files

All simulator data is externalised into JSON files. No business value is hardcoded.

```
AeroSim/main/
├── aircraft/aircrafts.json           → Aircraft fleet (type, speed, capacity)
├── airport/airports.json             → Airports, terminals, gates, runways, taxiway graph
├── airline/airlines.json             → Airlines (IATA, ICAO, country)
└── air_corridor/air_corridors.json   → Air corridors (distance, altitude, capacity, waypoints)
```

### Airport structure

An airport contains:
- **terminals**, each with a maximum aircraft capacity
- **gates**, linked to a terminal, able to host one aircraft
- **runways**, with their length and magnetic heading
- a **taxiway graph**: a graph of nodes (`gate`, `intersection`, `runway_threshold`) connected by edges weighted in metres

This graph is what enables taxiing path computation via the A* algorithm.

### Air corridor structure

```json
{
  "air_corridor_code": "CDG-LHR-N1",
  "from_airport": "<uuid>",
  "to_airport": "<uuid>",
  "distance": 340,
  "altitude": "FL310",
  "direction": "BIDIRECTIONAL",
  "max_capacity": 20,
  "waypoints": [...]
}
```

---

## A* Algorithm

The A* algorithm is used at two distinct levels in the simulator.

### 1. Ground taxiing: gate → runway (and runway → gate)

On departure, the simulator computes the optimal path between the departure gate and the assigned runway threshold, traversing the airport's taxiway graph. On arrival, the reverse path is computed to find the closest available gate.

The graph is made up of `Node` objects (gate, intersection, runway_threshold) connected by `Edge` objects weighted by their distance in metres. The heuristic function uses the Haversine distance between the current node and the goal node.

```python
# airport/application/taxiway_pathfinding_service.py
def find_path_graph(nodes, edges, start_id, goal_id) -> list[str]:
    ...
```

The best arrival gate selection (`find_best_landing_gate`) iterates over all free and compatible gates, computes the A* path from the runway threshold to each one, and keeps the one with the shortest total distance.

### 2. Air navigation: corridors and waypoints

In flight, the aircraft follows an air corridor containing an ordered sequence of geographical waypoints. Progression between waypoints is computed via great-circle interpolation (Haversine formula), and the position is updated on each tick based on cruising speed and the remaining time to estimated arrival.

In the future, the A* algorithm could be applied to the waypoint graph to dynamically compute alternative routes in the event of a waypoint closure or traffic conflict.

---

## `scheduled_flights`: departure and arrival ordering queue

Each runway maintains a `scheduled_flights` list that acts as a **priority-ordered queue**.

- **On departure**, flights are added to the assigned runway when they are created. The list is then sorted by priority (`FlightPriority.order`) and then by estimated departure time. Only the first flight in the queue is allowed to transition to `LINEUP`, then `TAKEOFF`. The others wait their turn.
- **On arrival**, descending flights are added to the arrival runway and sorted by estimated arrival time. The arrival runway is assigned dynamically during the cruise phase, by selecting the runway with the fewest flights already scheduled.

This structure makes it straightforward to simulate takeoff and landing sequencing without runway collisions, while respecting flight priorities (medical emergencies, fuel critical, etc.).

---

## Intentionally Overlooked Complexity

The following points have been identified but deliberately set aside to keep the first version functional:

- **In-flight separation bubbles**: there is no safety bubble computed in flight. Two aircraft could theoretically cross the same geographic point simultaneously.
- **Simultaneous runway capacity**: a runway is marked `OCCUPIED` during takeoff/landing, but the queue does not account for real runway clearing delays.
- **Differentiated fuel consumption**: the `fuel_burn_rate_kg_per_s` field exists in the `Flight` model but is not yet dynamically calculated based on aircraft type, flight phase, or weather.
- **Aircraft weight**: the `Aircraft` model does not account for takeoff weight (MTOW), which simplifies runway selection — in reality, a narrow-body may use a short runway while a wide-body cannot.
- **Real departure/arrival times**: airlines, slot management, and actual flight plans are not modelled.

---

## To Be Developed

### Traffic conflicts
Detect and resolve conflicts between flights sharing the same corridor or waypoints. Implement horizontal and vertical separation logic (flight levels) and avoidance manoeuvres.

### Weather incidents
Model turbulence zones, storm cells, or airspace restrictions that dynamically affect corridors. A corridor could switch to `RESTRICTED` or `CLOSED` mid-simulation, forcing flights to reroute.

### Waypoint closures
When a waypoint is closed (`WaypointStatus.CLOSED`), flights that were due to traverse it must recompute their route. This is where the A* algorithm on the waypoint graph becomes essential.

### Blocked taxiway nodes
A node in the taxiway graph can become unavailable (incident, vehicle, maintenance). The A* pathfinding must then recompute an alternative route in real time, excluding the blocked node.

### In-flight diversions
A flight in descent or cruise could be diverted to an alternate airport (go-around or diversion) if landing is impossible (closed runway, saturated traffic, weather). The `Flight` model already includes the necessary fields (`arrival_airport_code`, `dest_lat`, `dest_lon`).

### Aircraft weight impact on speed and runway selection
The aircraft's takeoff mass (passengers + fuel + cargo) should impact climb speed, required taxi distance, and therefore runway selection. A heavier aircraft requires a longer runway and will have a slower climb phase.

### Visualisation
A visualisation adapter is planned (`adapter/`) for each domain. The goal is to display in real time a simulation grid (aircraft positions, gate statuses, corridor flows) using **pygame** or **matplotlib**, with no dependency on an external server.

---

## Project Structure

```
AeroSim/
├── main/
│   ├── main.py
│   ├── flight/
│   │   ├── domain/          → Flight entity, enums (FlightStatus, FlightPriority, RunwayUsageType)
│   │   ├── application/     → Business services (physics, timing, factory, priority)
│   │   └── adapter/         → (planned: visualisation)
│   ├── aircraft/
│   │   ├── domain/          → Aircraft entity, AircraftType
│   │   └── application/
│   ├── airline/
│   │   ├── domain/          → Airline entity
│   │   └── application/
│   ├── airport/
│   │   ├── domain/          → Airport, Terminal, Gate, Runway, Node, Edge
│   │   ├── application/     → A* taxiway pathfinding, gate/runway assignment
│   │   └── adapter/
│   ├── air_corridor/
│   │   ├── domain/          → AirCorridor, CorridorStatus, CorridorDirection
│   │   ├── application/     → Available corridor lookup
│   │   └── adapter/
│   ├── waypoint/
│   │   ├── domain/          → Waypoint, WaypointStatus
│   │   └── application/
│   └── shared/
│       ├── bootstrap.py      → Data loading and simulator initialisation
│       ├── simulator.py      → Main simulation loop
│       ├── object_factory.py → JSON hydration → domain objects
│       ├── data_loader.py    → JSON file reading
│       └── init_logger.py    → Console logging and display
└── test/                     → To be completed
```

---

## Getting Started

```bash
git clone <repo_url>
pip install -r requirements.txt
pip install --upgrade -r requirements.txt
cd AeroSim/main
python main.py
```