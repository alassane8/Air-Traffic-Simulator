# Air Traffic Simulator — Documentation Technique

> Simulateur de trafic aérien temps-réel orienté physique de vol, GNC et cartographie.  
> Architecture hexagonale Python · pygame · 15 aéroports · 300 corridors · modèles ISA/Breguet/Haversine

![AeroSim Visualizer](screenshot.png)

---

## Table des matières

1. [Architecture générale](#1-architecture-générale)
2. [Démarrage rapide](#2-démarrage-rapide)
3. [Boucle de simulation](#3-boucle-de-simulation)
4. [Modèle atmosphérique ISA](#4-modèle-atmosphérique-isa)
5. [Aérodynamique — vitesse de décrochage](#5-aérodynamique--vitesse-de-décrochage)
6. [Contrôle de vitesse et marge de sécurité](#6-contrôle-de-vitesse-et-marge-de-sécurité)
7. [Modèle de carburant — équation de Breguet](#7-modèle-de-carburant--équation-de-breguet)
8. [Consommation par phase de vol](#8-consommation-par-phase-de-vol)
9. [Navigation sphérique — formule de Haversine](#9-navigation-sphérique--formule-de-haversine)
10. [Propagation de position — interpolation géodésique](#10-propagation-de-position--interpolation-géodésique)
11. [Modèle de montée/descente](#11-modèle-de-montéedescente)
12. [ETA complète du vol](#12-eta-complète-du-vol)
13. [Pathfinding taxiway — algorithme A*](#13-pathfinding-taxiway--algorithme-a)
14. [Constantes et paramètres de référence](#14-constantes-et-paramètres-de-référence)

---

## 1. Architecture générale

Le simulateur suit une **architecture hexagonale** : le cœur métier (domaines `aircraft`, `airport`, `flight`) est strictement séparé de l'infrastructure (visualizer pygame, chargement JSON). Cela permet de faire tourner la simulation sans affichage, ou de remplacer le renderer sans toucher à la physique.

```
main/
├── aircraft/          — Domaine appareil (masse, vitesse, ailes, carburant)
├── airport/           — Aéroports, pistes, terminaux, gates, taxiways
├── air_corridor/      — Corridors aériens ICAO avec waypoints
├── flight/            — Domaine vol + services physique/timing/fuel
└── shared/
    ├── simulator/
    │   ├── departure_simulator/   — Embarquement → décollage
    │   ├── flight_simulator/      — Croisière, montée, descente
    │   └── landing_simulator/     — Descente finale
    └── adapter/visualizer/        — Rendu pygame (carte, vols, HUD)
```

---

## 2. Démarrage rapide

```bash
# Dépendances
pip install pygame geodatasets geopandas shapely

# Lancer le simulateur
cd main
python main.py

# Visualizer seul (sans simulation)
python shared/adapter/visualizer/visualizer.py
```

**Contrôles visualizer :**

| Entrée | Action |
|---|---|
| Molette souris | Zoom centré sur curseur |
| Clic droit + drag | Pan |
| `+` / `-` | Zoom clavier |
| `R` | Reset vue monde |
| Clic gauche sur avion | Sélectionner vol |
| `ESC` | Désélectionner |
| `Q` | Quitter |

---

## 3. Boucle de simulation

La simulation avance par ticks discrets. Le temps simulé est découplé du temps réel grâce à un facteur d'échelle `TIME_SCALE`, ce qui permet de simuler plusieurs heures de trafic en quelques minutes.

À chaque tick de durée $\Delta t_{\text{réel}} = 1\,\text{s}$, le temps simulé avance de :

$$\Delta t_{\text{sim}} = \Delta t_{\text{réel}} \times \tau_{\text{scale}} = 1 \times 20 = 20\,\text{s}$$

![Boucle de simulation et cycle d'états](docs/diagrams/sim_loop_states.svg)

La séquence d'exécution à chaque tick est :

1. `_tick_runway()` — progression des vols au sol (PLANNED → BOARDING → LINEUP → TAKEOFF)
2. `_tick_flight()` — mise à jour physique de chaque vol en l'air (CLIMBING → CRUISE → DESCENDING)
3. `_tick_landing()` — gestion de la descente finale, du taxi et du turnaround
4. `visualizer.update()` + `visualizer.draw()` — rendu à 60 fps

**Paramètres de la boucle :**

| Paramètre | Valeur | Unité |
|---|---|---|
| `TICK_INTERVAL` | 1.0 | s (temps réel par tick) |
| `TIME_SCALE` | 20 | × (accélération simulation) |
| `SIM_TICK` | 20.0 | s simulés par tick |
| `FPS_TARGET` | 60 | frames/s |

---

## 4. Modèle atmosphérique ISA

L'air est moins dense en altitude : un avion à 10 000 m vole dans un air environ 3× plus léger qu'au sol. Cette densité est un paramètre central du simulateur — elle intervient dans le calcul de la vitesse de décrochage (§5) et de la consommation de carburant. Plutôt que d'utiliser une valeur fixe, le simulateur recalcule la densité à chaque tick en fonction de l'altitude courante via le modèle d'atmosphère standard internationale (ISA).

La densité est calculée par la loi polytropique de la troposphère ($h < 11\,000\,\text{m}$) :

$$\rho(h) = \rho_0 \left(1 - \frac{\Lambda \cdot h}{T_0}\right)^{\frac{g}{\Lambda R} - 1}$$

Implémentée sous forme compacte :

$$\boxed{\rho(h) = 1.225 \times \max\!\left(0,\; 1 - 2.2558 \times 10^{-5}\, h\right)^{4.2561} \quad [\text{kg/m}^3]}$$

![Modèle atmosphérique ISA — densité en fonction de l'altitude](docs/diagrams/isa_model.svg)

Les constantes numériques proviennent des paramètres ISA standard :
- $2.2558 \times 10^{-5} = \Lambda / T_0 = 0.0065 / 288.15$
- $4.2561 = g / (\Lambda R) = 9.80665 / (0.0065 \times 287.058)$

**Fichier :** `shared/simulator/flight_simulator/flight.py` — `_compute_rho()`

---

## 5. Aérodynamique — vitesse de décrochage

Un avion vole parce que ses ailes génèrent une portance $L$ qui compense son poids. En dessous d'une vitesse minimale appelée **vitesse de décrochage** $V_s$, la portance devient insuffisante et l'avion ne peut plus se maintenir en l'air. Le simulateur calcule $V_s$ à chaque tick pour s'assurer que la vitesse assignée reste toujours au-dessus de ce seuil, en tenant compte de la réduction de masse au fur et à mesure que le carburant est consommé.

À l'équilibre portance = poids :

$$L = W \implies \frac{1}{2} \rho V_s^2 S \, C_{L_{\max}} = m g$$

D'où :

$$\boxed{V_s = \sqrt{\frac{2\, m g}{\rho\, S\, C_{L_{\max}}}} \quad [\text{m/s}]}$$

## 6. Contrôle de vitesse et marge de sécurité

$$V_{\text{cruise,min}} = 1.3 \times V_s$$

$$V_{\text{flight}} = \max\!\left(V_{\text{cruise,aircraft}},\; 1.3 \times V_s\right) \times 3.6 \quad [\text{km/h}]$$

![Vitesse de décrochage Vs, marge 1.3× et configuration volets](docs/diagrams/vstall_safety.svg)

| Symbole | Définition | Unité |
|---|---|---|
| $m$ | Masse totale en opération (`fuel_kg` inclus) | kg |
| $g$ | Accélération gravitationnelle = 9.81 | m/s² |
| $\rho$ | Densité de l'air à l'altitude courante (§4) | kg/m³ |
| $S$ | Surface alaire (`wing_area_m2`) | m² |
| $C_{L_{\max}}$ | Coefficient de portance max (`CL_max`) | — |

Le $C_{L_{\max}}$ varie selon la configuration des volets :

| Configuration | $C_{L_{\max}}$ |
|---|---|
| Croisière (ailes propres) | 1.4 |
| Décollage (flaps partiels) | 2.0 |
| Atterrissage (flaps + slats) | 2.7 |

Ce calcul est répété à chaque tick en CRUISE : comme le carburant se consume, la masse diminue, $V_s$ baisse légèrement, et la vitesse peut être ajustée en conséquence.

**Fichiers :** `flight/application/flight_physics_service.py` — `compute_v_stall()` / `_update_v_stall()`

---

## 7. Modèle de carburant — équation de Breguet

Avant chaque départ, le simulateur calcule la quantité de carburant à embarquer. Cette quantité doit couvrir la distance du vol tout en restant dans les limites de masse de l'appareil. L'outil classique pour ce calcul est l'**équation de Breguet**, qui relie directement la consommation à la distance, la vitesse et l'efficacité aérodynamique de l'avion.

La quantité de carburant de croisière est :

$$\boxed{m_{\text{fuel,trip}} = W_0 \left(1 - e^{-\dfrac{R \cdot \text{TSFC}}{(L/D)\, V}}\right)}$$

**Convergence itérative (4 itérations) :**

$$m_{\text{fuel}}^{(k+1)} = \left(m_{\text{OEW}} + m_{\text{payload}} + m_{\text{phases}} + m_{\text{fuel}}^{(k)}\right) \cdot g \cdot \left(1 - e^{-\frac{R \cdot \text{TSFC}}{(L/D)\,V}}\right) / g$$

**Carburant total avec réserve réglementaire ICAO (Annexe 6) :**

$$m_{\text{total}} = \min\!\left(\left(m_{\text{trip}} + m_{\text{phases}}\right) \times 1.15,\; m_{\text{fuel,max}}\right)$$

![Équation de Breguet — convergence itérative et réserve ICAO](docs/diagrams/breguet_fuel.svg)

| Symbole | Définition | Valeur/Unité |
|---|---|---|
| $W_0 = m_0 g$ | Poids initial | N |
| $R$ | Distance du corridor | m |
| $\text{TSFC}$ | Thrust Specific Fuel Consumption | $1.8 \times 10^{-5}$ kg/(N·s) |
| $L/D$ | Finesse aérodynamique | — |
| $V$ | Vitesse croisière | m/s |

**Fichier :** `shared/simulator/departure_simulator/compute_fuel.py` — `compute_flight_fuel()`

---

## 8. Consommation par phase de vol

Un avion ne consomme pas à la même cadence selon ce qu'il fait : au décollage les moteurs sont à pleine puissance, en descente ils sont presque au ralenti. Le simulateur utilise un **facteur multiplicateur** par rapport au régime de croisière.

$$\dot{m}_{\text{fuel}}(\phi) = \dot{m}_{\text{cruise}} \times k_\phi \qquad \Delta m_{\text{fuel}} = \dot{m}_{\text{cruise}} \times k_\phi \times \Delta t_{\text{réel}}$$

![Profil de consommation par phase de vol](docs/diagrams/fuel_phases.svg)

| Phase $\phi$ | Facteur $k_\phi$ | Justification physique |
|---|---|---|
| `LINEUP` | 0.24 | Ralenti sol, APU |
| `TAKEOFF` | 3.30 | Poussée maximale |
| `CLIMBING` | 2.47 | ≈ $\dot{m}_{\text{climb}} / \dot{m}_{\text{cruise}}$ |
| `CRUISE` | 1.00 | Référence |
| `DESCENDING` | 0.29 | Moteurs réduits (idle descent) |
| `LANDING` | 0.35 | Inverseurs de poussée + approche |
| `TAXI` | 0.24 | Roulage arrivée |

**Alerte carburant critique :**

$$\frac{m_{\text{fuel}}}{\dot{m}_{\text{cruise}}} < 1800\,\text{s} \implies \mathtt{FUEL\_CRITICAL}$$

**Fichier :** `flight/application/flight_physics_service.py` — `update_flight_fuel()`

---

## 9. Navigation sphérique — formule de Haversine

La Terre est une sphère : la ligne droite sur une carte n'est pas le chemin le plus court entre deux aéroports. Le vrai plus court chemin est un **grand cercle** (orthodromie). Pour calculer la distance de ces arcs, le simulateur utilise la **formule de Haversine**.

$$a = \sin^2\!\frac{\Delta\varphi}{2} + \cos\varphi_1 \cos\varphi_2 \sin^2\!\frac{\Delta\lambda}{2}$$

$$\boxed{d = 2 R_\oplus \arcsin\!\sqrt{a}}$$

## 10. Propagation de position — interpolation géodésique

À chaque tick, l'avion est déplacé via une **interpolation sphérique (Slerp géodésique)** qui garantit qu'il reste exactement sur le grand cercle.

$$f = \frac{v_{\text{km/s}} \times \Delta t_{\text{sim}}}{d} \qquad A = \frac{\sin((1-f)\,\delta)}{\sin\delta} \qquad B = \frac{\sin(f\,\delta)}{\sin\delta}$$

$$\varphi = \arctan2\!\left(z,\, \sqrt{x^2+y^2}\right) \qquad \lambda = \arctan2(y,\, x)$$

![Haversine et Slerp géodésique — navigation sur grand cercle](docs/diagrams/haversine_slerp.svg)

**Utilisations dans le projet :**
- Distance entre aéroports pour le calcul de carburant (§7)
- Distance résiduelle en vol pour l'ETA (§12)
- Heuristique admissible $h(n)$ dans l'A\* taxiway (§13)

**Fichiers :** `flight/application/flight_physics_service.py` — `update_position()`

---

## 11. Modèle de montée/descente

À chaque tick, le simulateur calcule de combien l'avion peut progresser vers l'altitude cible de son prochain waypoint.

$$h_{\text{target}} = \frac{h_{\min} + h_{\max}}{2} \times 0.3048 \quad [\text{m}] \qquad \dot{h} = R_c \times 0.00508 \quad [\text{m/s}]$$

$$h^{(k+1)} = \begin{cases} h_{\text{target}} & \text{si } |h_{\text{target}} - h^{(k)}| \leq \dot{h} \times \Delta t_{\text{réel}} \\ h^{(k)} + \text{sign}(h_{\text{target}} - h^{(k)}) \times \dot{h} \times \Delta t_{\text{réel}} & \text{sinon} \end{cases}$$

**Fichier :** `shared/simulator/flight_simulator/flight.py` — `_update_altitude_toward()`

---

## 12. ETA complète du vol

L'heure d'arrivée estimée (ETA) somme les temps de tous les segments du trajet encore à parcourir.

$$d_{\text{total}} = \sum_{i=i_{\text{courant}}}^{N-1} \text{Haversine}(P_i, P_{i+1}) + \text{Haversine}(P_{N-1}, A_{\text{arr}})$$

$$t_{\text{restant}} = \frac{d_{\text{total}} / V_{\text{km/s}}}{\tau_{\text{scale}}} + t_{\text{descent}} + t_{\text{landing}} + t_{\text{taxi}} \qquad \text{ETA} = t_{\text{now}} + t_{\text{restant}}$$

**Fichier :** `flight/application/flight_timing_service.py` — `compute_full_eta()`

---

## 13. Pathfinding taxiway — algorithme A*

Lorsqu'un avion reçoit une piste de départ, le simulateur calcule l'itinéraire optimal sur les taxiways via l'algorithme **A\***.

$$f(n) = g(n) + h(n)$$

$$h(n) = 2 R_\oplus \arcsin\!\sqrt{\sin^2\!\frac{\Delta\varphi}{2} + \cos\varphi_n\cos\varphi_{\text{goal}}\sin^2\!\frac{\Delta\lambda}{2}}$$

![Pathfinding A* sur le graphe de taxiways](docs/diagrams/astar_taxiway.svg)

- $g(n)$ : coût cumulé depuis la gate (somme des distances en mètres)
- $h(n)$ : heuristique admissible = haversine jusqu'à la piste (ne surestime jamais)
- Complexité : $O((V + E) \log V)$ avec tas binaire

**Fichier :** `airport/application/taxiway_pathfinding_service.py` — `find_path_graph()`

---

## 14. Constantes et paramètres de référence

| Constante | Valeur | Source |
|---|---|---|
| $R_\oplus$ | 6 371 km | Rayon moyen terrestre (IUGG) |
| $\rho_0$ | 1.225 kg/m³ | ISA MSL |
| $T_0$ | 288.15 K | ISA MSL |
| $\Lambda$ | 0.0065 K/m | Gradient thermique ISA troposphère |
| $g$ | 9.80665 m/s² | Standard gravity |
| $R$ | 287.058 J/(kg·K) | Constante des gaz parfaits, air sec |
| TSFC | $1.8 \times 10^{-5}$ kg/(N·s) | Turbofan haute dilution typique |
| Réserve ICAO | 15 % | Annexe 6 ICAO |
| Masse pax + bagage | 95 kg | EASA CS-25 standard |
| $C_{L_{\max}}$ croisière | 1.4 | Profil typique turbofan |
| 1 ft | 0.3048 m | — |
| 1 ft/min | 0.00508 m/s | — |

---

*Document généré depuis le code source — toutes les formules reflètent l'implémentation effective.*