# ✈️ AeroSim — Air Traffic Simulation Engine

> A Python-based simulation engine modelling airport infrastructure, ATC decision-making, and real-time air traffic conflict resolution.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Domain](https://img.shields.io/badge/Domain-Aerospace%20%7C%20Simulation-0D1B2A?style=flat)

---

## 📌 Overview

**AeroSim** simulates the full lifecycle of air traffic around a major airport — from flight scheduling and runway assignment to real-time conflict detection and ATC (Air Traffic Control) decision-making.

The project is inspired by real-world systems used at **Eurocontrol**, **Thales Air Systems**, and the **CNES** (Centre National d'Études Spatiales), where simulation engines are critical tools for validating ATM (Air Traffic Management) algorithms before deployment.

The simulation is built around **Charles de Gaulle (CDG)** and **Paris-Orly (ORY)** airports, using real infrastructure data (runway lengths, headings, terminal capacities) sourced from OurAirports and OACI documentation.

---

## 🎯 Objectives

- Model the physical infrastructure of an airport (runways, terminals, gates) from structured configuration files
- Simulate the full lifecycle of a flight: `SCHEDULED → BOARDING → TAXIING → TAKEOFF → CRUISING → APPROACH → LANDING`
- Implement an ATC controller applying ICAO separation rules and priority-based runway assignment
- Detect and resolve trajectory conflicts using geometric vector-based algorithms
- Visualize live traffic on an interactive map with real-time metrics
- Benchmark multiple scheduling strategies (FCFS, priority-based, optimised heuristics)

---

## 🏗️ Architecture

AeroSim follows a strict **hexagonal architecture** (Ports & Adapters). The domain is completely isolated from infrastructure concerns — it has zero knowledge of JSON files, dashboards, or external APIs. All communication goes through ports (interfaces) implemented by adapters.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DRIVING ADAPTERS                             │
│         (they call the application — left side)                     │
│                                                                     │
│   ┌─────────────────┐          ┌─────────────────┐                 │
│   │   CLI Runner    │          │  Dash Dashboard  │                 │
│   │  simulator.py   │          │  dashboard.py    │                 │
│   └────────┬────────┘          └────────┬─────────┘                │
│            │                            │                           │
└────────────┼────────────────────────────┼───────────────────────────┘
             │  calls via                 │  reads via
             ▼  ISimulationPort           ▼  IMetricsPort
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                            │
│                    (use cases / services)                           │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    SimulationService                         │  │
│   │   ┌─────────────────┐  ┌───────────────┐  ┌──────────────┐  │  │
│   │   │  ATCController  │  │   Scheduler   │  │ConflictSolver│  │  │
│   │   │  atc_controller │  │  scheduler.py │  │conflict_     │  │  │
│   │   │      .py        │  │               │  │solver.py     │  │  │
│   │   └────────┬────────┘  └───────┬───────┘  └──────┬───────┘  │  │
│   └────────────┼───────────────────┼─────────────────┼──────────┘  │
│                │    operates on    │                  │             │
└────────────────┼───────────────────┼──────────────────┼─────────────┘
                 ▼                   ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DOMAIN LAYER                               │
│              (pure business logic — no dependencies)                │
│                                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│   │ Airport  │  │  Runway  │  │   Gate   │  │    Aircraft      │  │
│   │airport.py│  │runway.py │  │  gate.py │  │  aircraft.py     │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                                     │
│   ┌──────────────────────┐    ┌─────────────────────────────────┐  │
│   │      Terminal        │    │          SimState               │  │
│   │    terminal.py       │    │          state.py               │  │
│   └──────────────────────┘    └─────────────────────────────────┘  │
│                                                                     │
│         ┌──────────────────────────────────────┐                   │
│         │               PORTS                  │                   │
│         │  IAirportRepository  IEventLogger     │                   │
│         │  IFlightDataSource   IMetricsPort     │                   │
│         └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
                 ▲                   ▲                  ▲
                 │  implements       │                  │
┌────────────────┼───────────────────┼──────────────────┼─────────────┐
│                       DRIVEN ADAPTERS                               │
│         (called by the domain — right side)                         │
│                                                                     │
│   ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│   │  JsonAirport    │  │  CsvEventLogger  │  │ OpenSkyAdapter   │  │
│   │  Repository     │  │  logger.py       │  │ opensky.py       │  │
│   │  loader.py      │  │                  │  │                  │  │
│   └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│            │                    │                      │            │
└────────────┼────────────────────┼──────────────────────┼────────────┘
             ▼                    ▼                      ▼
      airports.json          events.csv           OpenSky API
      aircrafts.json         simulation.db        (ADS-B live)
```

### Project structure

```
aerosim/
│
├── domain/                         # ● DOMAIN — zero external dependencies
│   ├── models/
│   │   ├── airport.py
│   │   ├── terminal.py
│   │   ├── runway.py
│   │   ├── gate.py
│   │   └── aircraft.py
│   ├── services/
│   │   ├── atc_controller.py       # ATC logic: sequencing, priority, separation
│   │   ├── scheduler.py            # Flight queue management
│   │   └── conflict_solver.py      # Geometric conflict detection & resolution
│   ├── state.py                    # In-memory simulation state
│   └── ports/                      # Interfaces (abstract base classes)
│       ├── airport_repository.py   # IAirportRepository
│       ├── event_logger.py         # IEventLogger
│       ├── flight_data_source.py   # IFlightDataSource
│       └── metrics_port.py         # IMetricsPort
│
├── application/                    # ● APPLICATION — orchestrates use cases
│   └── simulation_service.py       # Main event loop, calls domain services
│
├── adapters/                       # ● ADAPTERS — implement ports
│   ├── driving/
│   │   ├── cli/
│   │   │   └── simulator.py        # Entry point: python -m aerosim
│   │   └── dashboard/
│   │       ├── dashboard.py        # Plotly Dash UI
│   │       └── map_view.py         # Folium trajectory map
│   └── driven/
│       ├── persistence/
│       │   ├── json_airport_repo.py  # Reads airports.json → domain objects
│       │   └── csv_event_logger.py   # Writes events.csv
│       └── external/
│           └── opensky_adapter.py    # OpenSky Network API → domain flights
│
├── data/
│   ├── airports.json               # Static airport config (CDG, ORY)
│   └── aircrafts.json              # Aircraft fleet definitions
│
├── tests/
│   ├── domain/
│   │   ├── test_atc_controller.py
│   │   └── test_conflict_solver.py
│   └── adapters/
│       └── test_json_airport_repo.py
│
├── logs/
│   └── events.csv
│
├── requirements.txt
└── README.md
```

### Key hexagonal principle

The domain **never imports** from `adapters/` or `data/`. Dependency arrows always point **inward** toward the domain. This means the entire simulation engine can be tested without any file I/O, external API, or UI — just pure Python objects.

```python
# ✅ correct — domain defines the interface
class IAirportRepository(ABC):
    @abstractmethod
    def load_all(self) -> List[Airport]: ...

# ✅ correct — adapter implements it
class JsonAirportRepository(IAirportRepository):
    def load_all(self) -> List[Airport]:
        # reads airports.json, returns domain objects

# ❌ never — domain must not know JSON exists
class ATCController:
    def __init__(self):
        with open("airports.json") as f:  # violation
            ...
```

---

## ⚙️ Core Concepts

### Airport Infrastructure

Airport configuration is loaded once at startup from `airports.json`. All dynamic state (runway occupancy, gate availability, terminal load) lives exclusively in memory during simulation — never written back to the config file.

```python
@dataclass
class Runway:
    id: str
    length: float       # metres
    heading: int        # magnetic heading (0–360°)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    # --- runtime state (never in JSON) ---
    status: str = "FREE"               # FREE | OCCUPIED | CLOSED | MAINTENANCE
    current_aircraft: Optional[str] = None
```

### ATC Controller

The ATC controller applies **ICAO Doc 4444** separation rules:

- Minimum runway separation: **90 seconds** between successive aircraft
- Priority queue: `EMERGENCY > FUEL_CRITICAL > MEDICAL > DELAY > NORMAL`
- Runway assignment based on wind heading and aircraft performance requirements
- Holding pattern management when terminal airspace (TMA) capacity is reached

### Conflict Detection

Trajectories are modelled as parametric vectors. The conflict solver projects positions N time-steps forward and flags pairs of aircraft violating ICAO minimums:

- Lateral separation: **3 NM (5.5 km)**
- Vertical separation: **1000 ft (300 m)**

Resolution strategies: speed adjustment, heading vector manoeuvre, or holding pattern assignment.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/your-username/aerosim.git
cd aerosim
pip install -r requirements.txt
```

### Run the simulation

```bash
python -m simulation.simulator
```

### Launch the dashboard

```bash
python -m visualization.dashboard
# Open http://localhost:8050
```

### Run tests

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## 📦 Tech Stack

| Category | Library | Usage |
|---|---|---|
| Core | Python 3.11, dataclasses | Domain modelling |
| Numerical | NumPy | Vector calculations, trajectory geometry |
| Geometry | Shapely | 2D spatial conflict detection |
| Data | Pandas | Log analysis, metrics computation |
| Visualisation | Plotly + Dash | Real-time interactive dashboard |
| Mapping | Folium | Trajectory rendering on real map tiles |
| Real data | OpenSky Network API | Live ADS-B flight positions |
| Testing | pytest, pytest-cov | Unit + integration tests |
| Logging | Loguru | Structured event logging |
| Config | Pydantic | Data validation on JSON load |

---

## 📊 Simulation Metrics

The engine tracks and exposes the following KPIs, comparable across scheduling strategies:

| Metric | Description |
|---|---|
| **Throughput** | Flights processed per simulated hour |
| **Average delay** | Actual landing time vs scheduled ETA |
| **Runway utilisation** | % of time each runway is occupied |
| **Conflict rate** | Conflicts detected per 100 flights |
| **Resolution rate** | % of conflicts resolved without human intervention |

---

## 🗺️ Roadmap

- [x] Airport infrastructure models (Runway, Gate, Terminal, Airport)
- [x] JSON configuration loader
- [ ] Aircraft model and flight lifecycle
- [ ] ATC controller with ICAO separation rules
- [ ] Priority-based flight scheduler
- [ ] Geometric conflict detection (2D)
- [ ] Conflict resolution (speed + heading adjustment)
- [ ] Plotly Dash real-time dashboard
- [ ] OpenSky Network integration (real flight data)
- [ ] 3D conflict detection (altitude layer)
- [ ] Strategy benchmark (FCFS vs optimised heuristic)
- [ ] Technical report + published article

---

## 🔗 Real-World Relevance

This project directly addresses technical challenges found in operational aerospace systems:

- **Eurocontrol** — European ATM network uses simulation engines to validate separation algorithms before live deployment
- **Thales Air Systems** — Develops ATC decision-support tools for major international airports
- **CNES** — Applies similar trajectory modelling and conflict avoidance logic to orbital mechanics and satellite collision avoidance
- **DSNA** (Direction des Services de la Navigation Aérienne) — French civil ATC authority, uses simulation for controller training

The domain vocabulary (ADS-B, TMA, TCAS, OACI Doc 4444, separation minima) used throughout this codebase is consistent with professional aerospace engineering standards.

---

## 📚 References & Data Sources

- [ICAO Doc 4444](https://www.icao.int) — PANS-ATM: Procedures for Air Navigation Services
- [OpenSky Network](https://opensky-network.org) — Free ADS-B flight data API and historical datasets
- [OurAirports](https://ourairports.com) — Open airport and runway database (CSV)
- [BlueSky ATC Simulator](https://github.com/TUDelft-CNS-ATM/bluesky) — Open-source reference simulator (TU Delft)
- [Eurocontrol BADA](https://www.eurocontrol.int/model/bada) — Aircraft performance model database

---

## 👤 Author

**Alassane WADE**
Fullstack Software Engineer — Paris, France
Specialising in geospatial systems, simulation, and applied aerospace software.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Alassane%20Wade-0077B5?style=flat&logo=linkedin)](https://linkedin.com/in/alassane-wade)
[![GitHub](https://img.shields.io/badge/GitHub-your--username-181717?style=flat&logo=github)](https://github.com/your-username)

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
