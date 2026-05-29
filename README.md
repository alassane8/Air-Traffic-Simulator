# Air Traffic Simulator

Simulateur de trafic aérien temps-réel que j'ai construit pour appliquer le plus de réalisme possible à chaque phase du vol — de l'embarquement au roulage à l'arrivée, en passant par la croisière à 10 000 m.

L'objectif du pprojet est de comprendre ce qui se passe vraiment quand un avion vole, et le modéliser équation par équation en tentant de négliger le moins d'élément possible pour obtenir un modèle proche d'une situation réelle.

---

## Ce que le simulateur couvre

Un trafic complet sur 15 aéroports et 300 corridors aériens, avec une physique recalculée à chaque tick :

- **Atmosphère** — modèle ISA, densité de l'air en fonction de l'altitude à chaque pas de simulation
- **Aérodynamique** — vitesse de décrochage recalculée en temps réel (portance, masse variable, configuration volets)
- **Carburant** — calcul pré-vol par équation de Breguet avec convergence itérative, consommation différenciée par phase (décollage ×3.3, ralenti ×0.24), réserve ICAO
- **Navigation** — great-circle via Haversine, propagation de position par interpolation géodésique (Slerp)
- **Montée / descente** — taux de montée par type d'appareil, transition altitude waypoint par waypoint
- **ETA** — recalculée à chaque tick sur la somme des segments restants
- **Pathfinding taxiway** — A\* géodésique de la gate à la piste
- **Visualisation** — rendu pygame temps réel avec sélection de vol et HUD

---

## Pourquoi ce projet

Je voulais savoir ce qui se cache derrière les chiffres qu'on voit sur FlightRadar24. Pourquoi un avion ralentit en montant, pourquoi la consommation explose au décollage, comment un dispatcher calcule le carburant à embarquer.

Chaque module a été l'occasion de creuser un vrai sujet : l'ISA et pourquoi la densité change tout à la portance, l'équation de Breguet et son caractère itératif (la masse de carburant dépend du poids total qui inclut le carburant), le grand cercle comme seule géométrie honnête sur une sphère.

L'objectif était un simulateur où les avions se comportent comme de vrais appareils — pas des points qui glissent sur une carte à vitesse constante.

---

## Architecture générale

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

## Démarrage rapide

```bash
pip install pygame geodatasets geopandas shapely

cd main
python main.py
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

## Boucle de simulation

La simulation avance par ticks discrets. Le temps simulé est découplé du temps réel via `TIME_SCALE`, ce qui permet de simuler plusieurs heures de trafic en quelques minutes.

À chaque tick de durée $\Delta t_{\text{réel}} = 1\,\text{s}$, le temps simulé avance de :

$$\Delta t_{\text{sim}} = \Delta t_{\text{réel}} \times \tau_{\text{scale}} = 1 \times 20 = 20\,\text{s}$$

**Paramètres de la boucle :**

| Paramètre | Valeur | Unité |
|---|---|---|
| `TICK_INTERVAL` | 1.0 | s (temps réel par tick) |
| `TIME_SCALE` | 20 | × (accélération simulation) |
| `SIM_TICK` | 20.0 | s simulés par tick |
| `FPS_TARGET` | 60 | frames/s |

---

## Modèle atmosphérique ISA

$$\boxed{\rho(h) = 1.225 \times \max\!\left(0,\; 1 - 2.2558 \times 10^{-5}\, h\right)^{4.2561} \quad [\text{kg/m}^3]}$$

**Fichier :** `shared/simulator/flight_simulator/flight.py` — `_compute_rho()`

---

## Aérodynamique — vitesse de décrochage

$$\boxed{V_s = \sqrt{\frac{2\, m g}{\rho\, S\, C_{L_{\max}}}} \quad [\text{m/s}]} \qquad V_{\text{flight}} = \max\!\left(V_{\text{cruise}},\; 1.3 \times V_s\right) \times 3.6 \quad [\text{km/h}]$$

| Configuration | $C_{L_{\max}}$ |
|---|---|
| Croisière | 1.4 |
| Décollage | 2.0 |
| Atterrissage | 2.7 |

**Fichier :** `flight/application/flight_physics_service.py` — `compute_v_stall()`

---

## Modèle de carburant — équation de Breguet

$$\boxed{m_{\text{fuel,trip}} = W_0 \left(1 - e^{-\dfrac{R \cdot \text{TSFC}}{(L/D)\, V}}\right)} \qquad m_{\text{total}} = \min\!\left(m_{\text{trip}} \times 1.15,\; m_{\text{fuel,max}}\right)$$

**Fichier :** `shared/simulator/departure_simulator/compute_fuel.py`

---

## Consommation par phase de vol

| Phase | Facteur $k_\phi$ |
|---|---|
| `TAKEOFF` | 3.30 |
| `CLIMBING` | 2.47 |
| `CRUISE` | 1.00 |
| `DESCENDING` | 0.29 |
| `LANDING` | 0.35 |
| `TAXI` / `LINEUP` | 0.24 |

**Fichier :** `flight/application/flight_physics_service.py` — `update_flight_fuel()`

---

## Navigation sphérique — Haversine & Slerp géodésique

$$\boxed{d = 2 R_\oplus \arcsin\!\sqrt{\sin^2\!\frac{\Delta\varphi}{2} + \cos\varphi_1 \cos\varphi_2 \sin^2\!\frac{\Delta\lambda}{2}}}$$

Position propagée à chaque tick par interpolation sur le grand cercle (Slerp géodésique).

**Fichier :** `flight/application/flight_physics_service.py` — `update_position()`

---

## Pathfinding taxiway — A*

$$f(n) = g(n) + h(n) \qquad h(n) = \text{Haversine}(n,\; \text{piste})$$

Complexité $O((V + E) \log V)$ avec tas binaire. **Fichier :** `airport/application/taxiway_pathfinding_service.py`

---

## Constantes de référence

| Constante | Valeur | Source |
|---|---|---|
| $R_\oplus$ | 6 371 km | IUGG |
| $\rho_0$ | 1.225 kg/m³ | ISA MSL |
| $g$ | 9.80665 m/s² | Standard gravity |
| TSFC | $1.8 \times 10^{-5}$ kg/(N·s) | Turbofan haute dilution |
| Réserve ICAO | 15 % | Annexe 6 ICAO |
| Masse pax + bagage | 95 kg | EASA CS-25 |