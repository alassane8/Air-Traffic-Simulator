# AeroSim

# AeroSim — Commandes
 
```bash
git clone <url_du_repo>
pip install -r requirements.txt
pip install --upgrade -r requirements.txt
cd AeroSim/main
python main.py
```
 
# Tests AeroSim

Ce dossier est réservé aux tests. À compléter par le développeur.

Structure suggérée :
- `test/flight/` → tests unitaires du domaine et de l'application flight
- `test/aircraft/` → tests unitaires aircraft
- `test/airport/` → tests unitaires airport (gate, runway, terminal, taxiway)
- `test/air_corridor/` → tests unitaires air_corridor
- `test/shared/` → tests d'intégration (factory, simulator, bootstrap)

```text
AeroSim/
├── main/
│   ├── main.py
│   ├── flight/
│   │   ├── domain/       → flight.py, flight_enums.py
│   │   ├── application/  → flight_service.py, flight_factory.py,
│   │   │                   flight_timing_service.py, flight_physics_service.py
│   │   └── adapter/      (vide, prêt pour visualisation)
│   ├── aircraft/
│   │   ├── domain/       → aircraft.py
│   │   ├── application/  (vide)
│   │   └── adapter/
│   ├── airline/
│   │   ├── domain/       → airline.py
│   │   ├── application/
│   │   └── adapter/
│   ├── airport/
│   │   ├── domain/       → airport.py, gate.py, terminal.py, runway.py, node.py, edge.py
│   │   ├── application/  → gate_assignment_service.py, runway_assignment_service.py,
│   │   │                   taxiway_pathfinding_service.py (A*)
│   │   └── adapter/
│   ├── air_corridor/
│   │   ├── domain/       → air_corridor.py
│   │   ├── application/  → corridor_service.py
│   │   └── adapter/
│   ├── waypoint/
│   │   ├── domain/       → waypoint.py (WaypointStatus converti en Enum propre)
│   │   ├── application/
│   │   └── adapter/
│   └── shared/           → bootstrap.py, simulator.py, object_factory.py,
│                           data_loader.py, init_logger.py
└── test/
└── .gitignore
└── README.md
└── requirements.txt
```
