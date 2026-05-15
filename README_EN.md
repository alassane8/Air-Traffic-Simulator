# Air Traffic Simulator — Technical Documentation

> Real-time physics-based air traffic simulator covering flight GNC, atmospheric modelling and cartographic rendering.  
> Hexagonal architecture · Python · pygame · 15 airports · 300 corridors · ISA / Breguet / Haversine models

![AeroSim Visualizer](screenshot.png)
---

## Table of Contents

1. [General Architecture](#1-general-architecture)
2. [Simulation Loop](#2-simulation-loop)
3. [ISA Atmospheric Model](#3-isa-atmospheric-model)
4. [Aerodynamics — Stall Speed](#4-aerodynamics--stall-speed)
5. [Speed Control and Safety Margin](#5-speed-control-and-safety-margin)
6. [Fuel Model — Breguet Range Equation](#6-fuel-model--breguet-range-equation)
7. [Phase-Dependent Fuel Burn](#7-phase-dependent-fuel-burn)
8. [Spherical Navigation — Haversine Formula](#8-spherical-navigation--haversine-formula)
9. [Position Propagation — Geodesic Interpolation](#9-position-propagation--geodesic-interpolation)
10. [Heading](#10-heading)
11. [Climb / Descent Model](#11-climb--descent-model)
12. [Full-Flight ETA](#12-full-flight-eta)
13. [Cartography — Mercator Projection](#13-cartography--mercator-projection)
14. [Zoom & Pan — Screen Transform](#14-zoom--pan--screen-transform)
15. [Taxiway Pathfinding — A* Algorithm](#15-taxiway-pathfinding--a-algorithm)
16. [Air Corridor Management](#16-air-corridor-management)
17. [Reference Constants and Parameters](#17-reference-constants-and-parameters)
18. [Quick Start](#18-quick-start)

---

## 1. General Architecture

```
main/
├── aircraft/          — Aircraft domain (mass, speed, wing, fuel)
├── airport/           — Airports, runways, terminals, gates, taxiways
├── air_corridor/      — ICAO air corridors with waypoints
├── flight/            — Flight domain + physics/timing/fuel services
└── shared/
    ├── simulator/
    │   ├── departure_simulator/   — Boarding → takeoff
    │   ├── flight_simulator/      — Cruise, climb, descent
    │   └── landing_simulator/     — Final descent
    └── adapter/visualizer/        — pygame renderer (map, flights, HUD)
```

**Loop parameters:**

| Parameter | Value | Unit |
|---|---|---|
| `TICK_INTERVAL` | 1.0 | s (real time per tick) |
| `TIME_SCALE` | 20 | × (simulation acceleration) |
| `SIM_TICK` | 20.0 | simulated s per tick |
| `FPS_TARGET` | 60 | frames/s |

---

## 2. Simulation Loop

Each tick of real duration $\Delta t_{\text{real}} = 1\,\text{s}$ advances simulated time by:

$$\Delta t_{\text{sim}} = \Delta t_{\text{real}} \times \tau_{\text{scale}} = 1 \times 20 = 20\,\text{s}$$

Execution sequence per tick:

1. `_tick_runway()` — ground flight progression (PLANNED → BOARDING → LINEUP → TAKEOFF)
2. `_tick_flight()` — physics update of every airborne flight (CLIMBING → CRUISE → DESCENDING)
3. `visualizer.update()` + `visualizer.draw()` — 60 fps rendering

---

## 3. ISA Atmospheric Model

Air density is computed from the International Standard Atmosphere (ISA) polytrophic law:

$$\rho(h) = \rho_0 \left(1 - \frac{\Lambda \cdot h}{T_0}\right)^{\frac{g}{\Lambda R} - 1}$$

Implemented in compact form (troposphere, $h < 11\,000\,\text{m}$):

$$\boxed{\rho(h) = 1.225 \times \max\!\left(0,\; 1 - 2.2558 \times 10^{-5}\, h\right)^{4.2561} \quad [\text{kg/m}^3]}$$

where $h$ is in metres, $\rho_0 = 1.225\,\text{kg/m}^3$ (MSL density, 15 °C, 101 325 Pa).

Exponent derivation:
- $2.2558 \times 10^{-5} = \Lambda / T_0 = 0.0065 / 288.15$
- $4.2561 = g / (\Lambda R) = 9.80665 / (0.0065 \times 287.058)$

**File:** `shared/simulator/flight_simulator/flight.py` — `_compute_rho()`

---

## 4. Aerodynamics — Stall Speed

Stall speed $V_s$ is the minimum speed at which lift $L$ equals weight $W$:

$$L = W \implies \frac{1}{2} \rho V_s^2 S \, C_{L_{\max}} = m g$$

Solving for $V_s$:

$$\boxed{V_s = \sqrt{\frac{2\, m g}{\rho\, S\, C_{L_{\max}}}} \quad [\text{m/s}]}$$

| Symbol | Definition | Unit |
|---|---|---|
| $m$ | Total operating mass (including `fuel_kg`) | kg |
| $g$ | Gravitational acceleration = 9.81 | m/s² |
| $\rho$ | Air density at current altitude | kg/m³ |
| $S$ | Wing area (`wing_area_m2`) | m² |
| $C_{L_{\max}}$ | Maximum lift coefficient (`CL_max`) | — |

**$C_{L_{\max}}$ by configuration:**

| Configuration | $C_{L_{\max}}$ |
|---|---|
| Cruise (clean wing) | 1.4 |
| Takeoff (partial flaps) | 2.0 |
| Landing (full flaps + slats) | 2.7 |

**File:** `flight/application/flight_physics_service.py` — `compute_v_stall()`

---

## 5. Speed Control and Safety Margin

Regulations require a 30 % safety margin above $V_s$:

$$V_{\text{cruise,min}} = 1.3 \times V_s$$

The speed assigned to a flight is:

$$V_{\text{flight}} = \max\!\left(V_{\text{cruise,aircraft}},\; 1.3 \times V_s\right) \times 3.6 \quad [\text{km/h}]$$

This is recomputed each CRUISE tick to account for fuel burn (decreasing mass → decreasing $V_s$).

**File:** `shared/simulator/flight_simulator/flight.py` — `_update_v_stall()`

---

## 6. Fuel Model — Breguet Range Equation

The cruise fuel burn is computed from the Breguet jet range equation:

$$\boxed{m_{\text{fuel,trip}} = W_0 \left(1 - e^{-\dfrac{R \cdot \text{TSFC}}{(L/D)\, V}}\right)}$$

| Symbol | Definition | Value/Unit |
|---|---|---|
| $W_0 = m_0 g$ | Initial weight (OEW + payload + phase fuel + fuel estimate) | N |
| $R$ | Corridor distance | m |
| $\text{TSFC}$ | Thrust Specific Fuel Consumption | $1.8 \times 10^{-5}$ kg/(N·s) |
| $L/D$ | Lift-to-drag ratio (`ld_ratio`) | — |
| $V$ | Cruise speed | m/s |

**Iterative convergence (4 iterations):**

Since $W_0$ depends on the fuel itself, the equation is solved by fixed-point iteration:

$$m_{\text{fuel}}^{(k+1)} = \left(m_{\text{OEW}} + m_{\text{payload}} + m_{\text{phases}} + m_{\text{fuel}}^{(k)}\right) \cdot g \cdot \frac{1 - e^{-\frac{R \cdot \text{TSFC}}{(L/D)\,V}}}{g}$$

Initialisation: $m_{\text{fuel}}^{(0)} = 5\,000\,\text{kg}$.

**Total fuel with ICAO regulatory reserve:**

$$m_{\text{total}} = \min\!\left(\left(m_{\text{trip}} + m_{\text{phases}}\right) \times 1.15,\; m_{\text{fuel,max}}\right)$$

**File:** `shared/simulator/departure_simulator/compute_fuel.py` — `compute_flight_fuel()`

---

## 7. Phase-Dependent Fuel Burn

The instantaneous burn rate is modulated by a phase factor $k_\phi$ relative to cruise:

$$\dot{m}_{\text{fuel}}(\phi) = \dot{m}_{\text{cruise}} \times k_\phi$$

$$\Delta m_{\text{fuel}} = \dot{m}_{\text{cruise}} \times k_\phi \times \Delta t_{\text{real}}$$

| Phase $\phi$ | Factor $k_\phi$ | Physical rationale |
|---|---|---|
| `LINEUP` | 0.24 | Ground idle, APU running |
| `TAKEOFF` | 3.30 | Max thrust, near full power |
| `CLIMBING` | 2.47 | ≈ $\dot{m}_{\text{climb}} / \dot{m}_{\text{cruise}}$ |
| `CRUISE` | 1.00 | Reference |
| `DESCENDING` | 0.29 | Idle descent, throttle reduced |
| `LANDING` | 0.35 | Thrust reversers + approach |
| `TAXI` | 0.24 | Arrival taxi, ground idle |

**Fuel critical alert:** triggered when remaining fuel provides less than 30 minutes of cruise endurance:

$$\frac{m_{\text{fuel}}}{\dot{m}_{\text{cruise}}} < 1800\,\text{s} \implies \texttt{FUEL\_CRITICAL}$$

**File:** `flight/application/flight_physics_service.py` — `update_flight_fuel()`

---

## 8. Spherical Navigation — Haversine Formula

The orthodromic (great-circle) distance between two geographic points is computed using the Haversine formula, numerically stable for both short and long distances:

$$a = \sin^2\!\frac{\Delta\varphi}{2} + \cos\varphi_1 \cos\varphi_2 \sin^2\!\frac{\Delta\lambda}{2}$$

$$\boxed{d = 2 R_\oplus \arcsin\!\sqrt{a}}$$

where $R_\oplus = 6\,371\,\text{km}$, $\varphi$ = latitude in radians, $\lambda$ = longitude in radians.

**Numerical precision:** $a$ is clamped to $[0, 1]$ to avoid invalid $\arcsin$ domains due to floating-point rounding.

**Uses in the project:**
- Airport-to-airport distance for fuel calculation
- Residual distance for ETA during cruise
- A* taxiway heuristic $h(n)$ (see §15)

**Files:** `flight/application/flight_physics_service.py`, `airport/application/taxiway_pathfinding_service.py`

---

## 9. Position Propagation — Geodesic Interpolation

At each simulation tick, position is propagated along the great circle from current position $P_1(\varphi_1, \lambda_1)$ to destination $P_2(\varphi_2, \lambda_2)$.

**Path fraction covered per tick:**

$$f = \frac{v_{\text{km/s}} \times \Delta t_{\text{sim}}}{d}$$

where $v_{\text{km/s}} = V_{\text{flight}} / 3600$ and $d$ is the current orthodromic distance.

**Spherical interpolation (geodesic Slerp):**

Let $\delta = 2\arcsin\sqrt{a}$ be the central angle between both points. Interpolation coefficients are:

$$A = \frac{\sin((1-f)\,\delta)}{\sin\delta}, \qquad B = \frac{\sin(f\,\delta)}{\sin\delta}$$

Interpolated ECEF Cartesian coordinates:

$$\begin{pmatrix} x \\ y \\ z \end{pmatrix} = A \begin{pmatrix} \cos\varphi_1\cos\lambda_1 \\ \cos\varphi_1\sin\lambda_1 \\ \sin\varphi_1 \end{pmatrix} + B \begin{pmatrix} \cos\varphi_2\cos\lambda_2 \\ \cos\varphi_2\sin\lambda_2 \\ \sin\varphi_2 \end{pmatrix}$$

Back to geographic coordinates:

$$\boxed{\varphi = \arctan2\!\left(z,\, \sqrt{x^2+y^2}\right), \qquad \lambda = \arctan2(y,\, x)}$$

This method guarantees the aircraft follows the exact great circle without drift from successive spherical integrations.

**Adaptive speed:** when `estimated_arrival_time` lies in the future, speed is dynamically recomputed:

$$v_{\text{km/s}} = \frac{d}{t_{\text{remaining}}}$$

**File:** `flight/application/flight_physics_service.py` — `update_position()`

---

## 10. Heading

The magnetic heading (initial great-circle bearing) is computed by the orthodromic bearing formula:

$$\theta = \arctan2\!\left(\sin\Delta\lambda \cos\varphi_2,\; \cos\varphi_1\sin\varphi_2 - \sin\varphi_1\cos\varphi_2\cos\Delta\lambda\right)$$

converted to degrees in $[0°, 360°)$ for rendering the aircraft triangle icon in the visualizer.

---

## 11. Climb / Descent Model

Altitude is adjusted progressively toward the current waypoint's target altitude, limited by the aircraft's rated climb rate.

**Waypoint target altitude:**

$$h_{\text{target}} = \frac{h_{\min} + h_{\max}}{2} \times 0.3048 \quad [\text{m}]$$

(midpoint of the FL range in feet, converted to metres: $1\,\text{ft} = 0.3048\,\text{m}$)

**Climb rate conversion:**

$$\dot{h} = R_c \times 0.00508 \quad [\text{m/s}]$$

where $R_c$ is in ft/min ($1\,\text{ft/min} = 0.00508\,\text{m/s}$).

**Altitude update per tick:**

$$\Delta h_{\max} = \dot{h} \times \Delta t_{\text{real}}$$

$$h^{(k+1)} = \begin{cases} h_{\text{target}} & \text{if } |h_{\text{target}} - h^{(k)}| \leq \Delta h_{\max} \\ h^{(k)} + \text{sign}(h_{\text{target}} - h^{(k)}) \times \Delta h_{\max} & \text{otherwise} \end{cases}$$

**File:** `shared/simulator/flight_simulator/flight.py` — `_update_altitude_toward()`

---

## 12. Full-Flight ETA

The estimated time of arrival is computed by summing the distances of all remaining segments (waypoints + destination airport):

$$d_{\text{total}} = \sum_{i=i_{\text{current}}}^{N-1} \text{Haversine}(P_i, P_{i+1}) + \text{Haversine}(P_{N-1}, A_{\text{arr}})$$

$$t_{\text{remaining}} = \frac{d_{\text{total}} / V_{\text{km/s}}}{\tau_{\text{scale}}} + t_{\text{descent}} + t_{\text{landing}} + t_{\text{taxi}}$$

$$\text{ETA} = t_{\text{now}} + t_{\text{remaining}}$$

This ETA is recalculated each CRUISE tick to reflect actual speed variations and progression.

**File:** `flight/application/flight_timing_service.py` — `compute_full_eta()`

---

## 13. Cartography — Mercator Projection

Web Mercator projection (EPSG:3857) is used for rendering. Latitude $\varphi$ is mapped to normalised ordinate $n_y \in [0, 1]$:

$$\psi(\varphi) = \ln\!\left(\tan\!\frac{\pi}{4} + \frac{\varphi}{2}\right) \quad \text{(Mercator ordinate)}$$

$$\psi_{\max} = \ln\!\left(\tan\!\frac{\pi}{4} + \frac{85°}{2}\right)$$

$$\boxed{n_y = \frac{1}{2} - \frac{\psi(\varphi)}{2\,\psi_{\max}}}$$

Longitude is projected linearly:

$$n_x = \frac{\lambda + 180°}{360°}$$

**Inverse projection** (pixel → geography, used for cursor coordinate display):

$$\varphi = 2\arctan\!\left(e^{\psi}\right) - \frac{\pi}{2}, \qquad \psi = (1 - n_y) \times 2\psi_{\max} - \psi_{\max}$$

The projection is clamped to $\pm 85°$ latitude to avoid the polar singularity ($\psi \to \pm\infty$).

**File:** `shared/adapter/visualizer/renderer/world_map.py`

---

## 14. Zoom & Pan — Screen Transform

The screen transform applies a centred zoom and camera offset:

**Normalised → pixel with zoom/pan:**

$$\begin{pmatrix} p_x \\ p_y \end{pmatrix} = \begin{pmatrix} (n_x \cdot W - c_x) \cdot z + c_x - \delta_x \\ (n_y \cdot H - c_y) \cdot z + c_y - \delta_y \end{pmatrix}$$

where $(c_x, c_y) = (W/2, H/2)$ is the window centre, $z$ is the zoom factor, $(\delta_x, \delta_y)$ is the pan offset.

**Zoom-to-pointer** — pan update to keep the cursor point $(m_x, m_y)$ fixed after zoom change $z \to z'$:

$$\delta_x' = \frac{z'}{z}\,(\delta_x + m_x - c_x) - (m_x - c_x)$$
$$\delta_y' = \frac{z'}{z}\,(\delta_y + m_y - c_y) - (m_y - c_y)$$

**Pan constraint** (prevent panning outside map bounds):

$$|\delta_x| \leq \frac{(z-1) \cdot W}{2}, \qquad |\delta_y| \leq \frac{(z-1) \cdot H}{2}$$

**Inverse projection with zoom/pan** (pixel → geography):

$$n_x = \frac{(p_x + \delta_x - c_x) / z + c_x}{W}, \qquad n_y = \frac{(p_y + \delta_y - c_y) / z + c_y}{H}$$

**File:** `shared/adapter/visualizer/visualizer.py`

---

## 15. Taxiway Pathfinding — A* Algorithm

Optimal path search on the taxiway graph (gate → runway threshold) uses A* with an admissible Haversine heuristic.

**Total cost function:**

$$f(n) = g(n) + h(n)$$

- $g(n)$: cumulative cost from source (sum of traversed edge distances in metres)
- $h(n)$: admissible heuristic = Haversine distance in metres to the goal

$$h(n) = 2 R_\oplus \arcsin\!\sqrt{\sin^2\!\frac{\Delta\varphi}{2} + \cos\varphi_n\cos\varphi_{\text{goal}}\sin^2\!\frac{\Delta\lambda}{2}}$$

The heuristic is admissible because the Haversine distance is the minimum distance on the sphere, never exceeding any actual path distance on the taxiway graph.

**Graph structure:**
- Nodes: gates, intersections, runway thresholds
- Edges: taxiway segments with distance in metres
- Undirected graph (bidirectional traversal)

**Complexity:** $O((V + E) \log V)$ with binary heap.

**File:** `airport/application/taxiway_pathfinding_service.py` — `find_path_graph()`

---

## 16. Air Corridor Management

**Random destination selection:** to prevent all flights from routing to the same destination, selection is two-stage:

1. Build the set of reachable destinations from departure airport $A$:

$$\mathcal{D}(A) = \left\{ \text{dest}(c) \mid c \in \mathcal{C},\; c.\text{has\_capacity}() \wedge c.\text{is\_open}() \wedge (c.from = A \vee (c.dir = \text{BIDI} \wedge c.to = A)) \right\}$$

2. Sample uniformly $d \sim \mathcal{U}(\mathcal{D}(A))$, then sample uniformly a corridor $c \sim \mathcal{U}(\{c \mid \text{dest}(c) = d\})$.

**Bidirectional support:** a corridor $A \to B$ with `direction = BIDIRECTIONAL` can be flown in both directions. When departing from $B$, the assigned arrival airport is $A$:

$$\text{arrival\_airport} = \begin{cases} c.to & \text{if } c.from = \text{depart} \\ c.from & \text{if } c.to = \text{depart} \land c.dir = \text{BIDI} \end{cases}$$

**File:** `air_corridor/application/corridor_service.py`

---

## 17. Reference Constants and Parameters

| Constant | Value | Source |
|---|---|---|
| $R_\oplus$ | 6 371 km | Mean Earth radius (IUGG) |
| $\rho_0$ | 1.225 kg/m³ | ISA MSL |
| $T_0$ | 288.15 K | ISA MSL |
| $\Lambda$ | 0.0065 K/m | ISA temperature lapse rate |
| $g$ | 9.80665 m/s² | Standard gravity |
| $R$ | 287.058 J/(kg·K) | Specific gas constant, dry air |
| TSFC | $1.8 \times 10^{-5}$ kg/(N·s) | Typical high-bypass turbofan |
| ICAO reserve | 15 % | ICAO Annex 6 |
| Pax + baggage | 95 kg | EASA CS-25 standard |
| $C_{L_{\max}}$ cruise | 1.4 | Typical turbofan airfoil |
| 1 ft | 0.3048 m | — |
| 1 ft/min | 0.00508 m/s | — |

---

## 18. Quick Start

```bash
# Install dependencies
pip install pygame geodatasets geopandas shapely

# Run the simulator
cd main
python main.py

# Visualizer only (without simulation)
python shared/adapter/visualizer/visualizer.py
```

**Visualizer controls:**

| Input | Action |
|---|---|
| Mouse wheel | Zoom centred on cursor |
| Right-click + drag | Pan |
| `+` / `-` | Keyboard zoom |
| `R` | Reset world view |
| Left-click on aircraft | Select flight |
| `ESC` | Deselect |
| `Q` | Quit |

---

*Document generated from source code — all formulae reflect actual implementation.*