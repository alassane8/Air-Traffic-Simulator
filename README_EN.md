# Air Traffic Simulator

A real-time air traffic simulator I built to apply as much realism as possible to every phase of flight — from boarding and pushback all the way through cruise at 10,000 m and back to gate.

The goal of the project is to understand what really happens when an airplane flies, and to model it equation by equation, trying to neglect as few elements as possible to obtain a model close to a real situation.
---

## What the simulator covers

Full traffic across 15 airports and 300 air corridors, with physics recomputed every tick:

- **Atmosphere** — ISA model, air density as a function of altitude at each simulation step
- **Aerodynamics** — stall speed recomputed in real time (lift, variable mass, flap configuration)
- **Fuel** — pre-flight calculation via Breguet range equation with iterative convergence, phase-differentiated burn rates (takeoff ×3.3, idle ×0.24), ICAO reserves
- **Navigation** — great-circle distance via Haversine, position propagation via geodesic Slerp interpolation
- **Climb / descent** — aircraft-specific climb rates, altitude transitions waypoint by waypoint
- **ETA** — recomputed every tick over the sum of remaining segments
- **Taxiway pathfinding** — geodesic A\* from gate to runway
- **Visualization** — real-time pygame rendering with zoom, pan, flight selection and HUD

---

## Why this project

I wanted to understand what's behind the numbers you see on FlightRadar24. Why a plane slows down while climbing, why fuel burn spikes at takeoff, how a dispatcher figures out how much fuel to load.

Each module became an opportunity to dig into something real: ISA and why air density changes everything for lift, the Breguet equation and why it's iterative (fuel mass depends on total weight which includes the fuel itself), the great circle as the only honest geometry on a sphere.

The goal was a simulator where aircraft behave like real machines — not dots sliding across a map at constant speed.

---

## Architecture

The simulator follows a **hexagonal architecture**: the business core (domains `aircraft`, `airport`, `flight`) is strictly separated from infrastructure (pygame visualizer, JSON loading). This allows running the simulation headless, or swapping the renderer without touching the physics.

```
main/
├── aircraft/          — Aircraft domain (mass, speed, wings, fuel)
├── airport/           — Airports, runways, terminals, gates, taxiways
├── air_corridor/      — ICAO air corridors with waypoints
├── flight/            — Flight domain + physics/timing/fuel services
└── shared/
    ├── simulator/
    │   ├── departure_simulator/   — Boarding → takeoff
    │   ├── flight_simulator/      — Cruise, climb, descent
    │   └── landing_simulator/     — Final approach & landing
    └── adapter/visualizer/        — pygame rendering (map, flights, HUD)
```

---

## Quick start

```bash
pip install pygame geodatasets geopandas shapely

cd main
python main.py
```

**Visualizer controls:**

| Input | Action |
|---|---|
| Mouse wheel | Zoom centered on cursor |
| Right click + drag | Pan |
| `+` / `-` | Keyboard zoom |
| `R` | Reset world view |
| Left click on aircraft | Select flight |
| `ESC` | Deselect |
| `Q` | Quit |

---

## Simulation loop

The simulation advances in discrete ticks. Simulated time is decoupled from real time via `TIME_SCALE`, allowing several hours of traffic to run in minutes.

At each tick of duration $\Delta t_{\text{real}} = 1\,\text{s}$, simulated time advances by:

$$\Delta t_{\text{sim}} = \Delta t_{\text{real}} \times \tau_{\text{scale}} = 1 \times 20 = 20\,\text{s}$$

**Loop parameters:**

| Parameter | Value | Unit |
|---|---|---|
| `TICK_INTERVAL` | 1.0 | s (real time per tick) |
| `TIME_SCALE` | 20 | × (simulation speedup) |
| `SIM_TICK` | 20.0 | simulated s per tick |
| `FPS_TARGET` | 60 | frames/s |

---

## ISA atmospheric model

$$\boxed{\rho(h) = 1.225 \times \max\!\left(0,\; 1 - 2.2558 \times 10^{-5}\, h\right)^{4.2561} \quad [\text{kg/m}^3]}$$

**File:** `shared/simulator/flight_simulator/flight.py` — `_compute_rho()`

---

## Aerodynamics — stall speed

$$\boxed{V_s = \sqrt{\frac{2\, m g}{\rho\, S\, C_{L_{\max}}}} \quad [\text{m/s}]} \qquad V_{\text{flight}} = \max\!\left(V_{\text{cruise}},\; 1.3 \times V_s\right) \times 3.6 \quad [\text{km/h}]$$

| Configuration | $C_{L_{\max}}$ |
|---|---|
| Cruise (clean) | 1.4 |
| Takeoff (partial flaps) | 2.0 |
| Landing (flaps + slats) | 2.7 |

**File:** `flight/application/flight_physics_service.py` — `compute_v_stall()`

---

## Fuel model — Breguet range equation

$$\boxed{m_{\text{fuel,trip}} = W_0 \left(1 - e^{-\dfrac{R \cdot \text{TSFC}}{(L/D)\, V}}\right)} \qquad m_{\text{total}} = \min\!\left(m_{\text{trip}} \times 1.15,\; m_{\text{fuel,max}}\right)$$

**File:** `shared/simulator/departure_simulator/compute_fuel.py`

---

## Fuel burn by flight phase

| Phase | Factor $k_\phi$ |
|---|---|
| `TAKEOFF` | 3.30 |
| `CLIMBING` | 2.47 |
| `CRUISE` | 1.00 |
| `DESCENDING` | 0.29 |
| `LANDING` | 0.35 |
| `TAXI` / `LINEUP` | 0.24 |

**File:** `flight/application/flight_physics_service.py` — `update_flight_fuel()`

---

## Spherical navigation — Haversine & geodesic Slerp

$$\boxed{d = 2 R_\oplus \arcsin\!\sqrt{\sin^2\!\frac{\Delta\varphi}{2} + \cos\varphi_1 \cos\varphi_2 \sin^2\!\frac{\Delta\lambda}{2}}}$$

Position propagated each tick via great-circle interpolation (geodesic Slerp).

**File:** `flight/application/flight_physics_service.py` — `update_position()`

---

## Taxiway pathfinding — A*

$$f(n) = g(n) + h(n) \qquad h(n) = \text{Haversine}(n,\; \text{runway})$$

Complexity $O((V + E) \log V)$ with binary heap. **File:** `airport/application/taxiway_pathfinding_service.py`

---

## Reference constants

| Constant | Value | Source |
|---|---|---|
| $R_\oplus$ | 6,371 km | IUGG |
| $\rho_0$ | 1.225 kg/m³ | ISA MSL |
| $g$ | 9.80665 m/s² | Standard gravity |
| TSFC | $1.8 \times 10^{-5}$ kg/(N·s) | High-bypass turbofan |
| ICAO reserve | 15% | Annex 6 ICAO |
| Pax + baggage mass | 95 kg | EASA CS-25 |