# Air-Traffic-Simulator

La visualisation du simulateur est réalisée avec **pygame** pour le rendu graphique temps réel et **geopandas** pour l'affichage des côtes et la projection cartographique Mercator.

![AeroSim Visualizer](screenshot.png)

Air-Traffic-Simulator est un simulateur de trafic aérien écrit en Python, conçu pour modéliser de manière réaliste le cycle de vie complet d'un vol, depuis l'assignation à une gate jusqu'à l'atterrissage et le retour à quai. Le projet est structuré selon une **architecture hexagonale** (Ports & Adapters), avec une séparation claire entre domaine, logique métier et infrastructure.

---

## Hypothèses du projet

Le simulateur repose sur plusieurs hypothèses de conception choisies pour maintenir un niveau de complexité gérable dans un premier temps afin de se concentrer sur l'orchestration des vols et l'attributions des pistes de décollage et d'atterrissage:

- **Un avion = un vol à la fois.** Un aéronef est assigné à une gate, génère un vol, décolle, atterrit, et redevient disponible. Il n'y a pas de rotation multi-étapes modélisée.
- **Les fichiers JSON sont la source de vérité.** Tous les aéroports, avions, compagnies et corridors sont définis statiquement dans des fichiers de configuration. Il n'y a pas de base de données.
- **Le temps est accéléré via un `TIME_SCALE`.** Un tick de simulation correspond à `TICK_INTERVAL * TIME_SCALE` secondes simulées. Par défaut, `TIME_SCALE = 60`, ce qui signifie qu'une seconde réelle représente une minute simulée.
- **La physique de vol est partiellement simplifiée.** La position géographique est interpolée via la formule de Haversine sur un grand cercle. Il n'y a pas de simulation de vent ou de turbulences. En revanche, la **densité de l'air (ρ) est calculée via le modèle ISA standard** à chaque tick, ce qui permet d'adapter la vitesse minimale de décrochage (`v_stall`) en fonction de l'altitude réelle du vol.
- **Les corridors sont bidirectionnels par défaut.** Un corridor peut être parcouru dans les deux sens sauf indication contraire dans la configuration.
- **La priorité d'un vol est tirée aléatoirement** selon une distribution pondérée (84 % `NORMAL`, 10 % `DELAY`, etc.), reflétant la réalité statistique du trafic aérien.

---

## Fichiers de configuration

Toute la donnée du simulateur est externalisée dans des fichiers JSON. Aucune valeur métier n'est codée en dur dans le code.

```
Air-Traffic-Simulator/main/
├── config/aircrafts.json         → Flotte d'avions (type, vitesse, capacité, masse, finesse)
        ├── airports.json         → Aéroports, terminaux, gates, runways, taxiway graph
        ├── airlines.json         → Compagnies aériennes (IATA, ICAO, pays)
        └── air_corridors.json    → Corridors aériens (distance, altitude, capacité, waypoints)
```

### Structure d'un aéroport

Un aéroport contient :
- des **terminaux**, chacun avec une capacité maximale d'avions
- des **gates**, liées à un terminal, pouvant accueillir un avion
- des **runways**, avec leur longueur et leur cap magnétique
- un **taxiway graph** : un graphe de nœuds (`gate`, `intersection`, `runway_threshold`) reliés par des arêtes pondérées en mètres

C'est ce graphe qui permet de calculer les chemins de roulage via l'algorithme A*.

### Structure d'un corridors aérien

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

## Algorithme A*

L'algorithme A* est utilisé à deux niveaux distincts dans le simulateur.

### 1. Roulage au sol : gate → runway (et runway → gate)

Lors du départ, le simulateur calcule le chemin optimal entre la gate de départ et le seuil de piste assigné, en traversant le taxiway graph de l'aéroport. À l'arrivée, le chemin inverse est calculé pour trouver la gate la plus proche disponible.

Le graphe est constitué de `Node` (gate, intersection, runway_threshold) reliés par des `Edge` pondérés par leur distance en mètres. La fonction heuristique utilise la distance de Haversine entre le nœud courant et le nœud objectif.

```python
# airport/application/taxiway_pathfinding_service.py
def find_path_graph(nodes, edges, start_id, goal_id) -> list[str]:
    ...
```

La sélection de la meilleure gate d'arrivée (`find_best_landing_gate`) itère sur toutes les gates libres et compatibles, calcule le chemin A* depuis le seuil de piste vers chacune, et retient celle dont la distance totale est minimale.

### 2. Navigation aérienne : corridors et waypoints

En vol, l'avion suit un corridor aérien qui contient une séquence ordonnée de waypoints géographiques. La navigation se déroule désormais **waypoint par waypoint** :

1. **Au décollage** (`_do_takeoff`), `dest_lat/dest_lon` est initialisé sur le **premier waypoint** du corridor (et non sur l'aéroport d'arrivée).
2. **En CRUISE**, à chaque fois que le vol atteint sa destination courante, il avance vers le waypoint suivant. Une fois tous les waypoints franchis, il cap sur l'aéroport d'arrivée (`current_waypoint_index == n_waypoints`).
3. **À l'arrivée à l'aéroport**, `_do_start_descent` est déclenché et le vol passe en `DESCENDING`.

La progression entre points est calculée via interpolation sur grand cercle (formule de Haversine sphérique), et la position est mise à jour à chaque tick.

À terme, l'algorithme A* pourra être appliqué sur le graphe des waypoints pour calculer dynamiquement des routes alternatives en cas de fermeture de waypoint ou de conflit de trafic.

---

## Calcul du carburant : formule de Breguet

Le carburant de chaque vol est calculé une seule fois, lors du **boarding**, juste avant que l'avion ne passe en `LINEUP`. Ce calcul produit deux valeurs stockées dans l'objet `Flight` :

- `flight.fuel_kg` — la quantité totale de carburant chargée à bord (kg)
- `flight.fuel_burn_rate_kg_per_s` — le débit de consommation en croisière (kg/s), utilisé ensuite à chaque tick pour décrémenter le carburant

Le service responsable est `compute_flight_fuel`, situé dans :

```
shared/simulator/departure_simulator/compute_fuel.py
```

Il est appelé dans `_tick_runway` au premier tick de la phase `BOARDING` :

```python
elif flight.status == FlightStatus.BOARDING:
    if flight.time_spent == 0:
        aircraft = aircrafts.get(flight.aircraft_id)
        if aircraft:
            init_aircraft_boarding(aircraft, flight, air_corridors)
```

### Méthode de calcul

Le calcul se décompose en trois étapes.

**1. Fuel des phases sol et transition**

Pour chaque phase du vol (lineup, décollage, montée, descente, atterrissage, taxi), la consommation est estimée à partir d'un débit fixe défini par type d'avion (`aircraft.BASE_FUEL_FLOW`) multiplié par la durée réglementaire de la phase :

```python
phase_fuel_kg = sum(
    aircraft.BASE_FUEL_FLOW.get(phase, 0.0) * duration
    for phase, duration in phase_durations.items()
)
```

**2. Fuel croisière via la formule de Breguet**

La consommation en croisière est calculée par la formule de Breguet Range, standard de l'ingénierie aéronautique :

```
fuel_trip = W_initial × (1 - exp(-R × TSFC / (L/D × V)))
```

Avec :
- `R` — distance du corridor en mètres
- `TSFC` — consommation spécifique de poussée, fixée à `0.000018 kg/(N·s)`
- `L/D` — finesse aérodynamique de l'appareil (`aircraft.ld_ratio`)
- `V` — vitesse de croisière en m/s
- `W_initial` — masse initiale de l'avion au décollage (masse à vide + payload + carburant estimé)

Comme `W_initial` dépend lui-même du carburant à calculer, la convergence est obtenue par **4 itérations successives**, en partant d'une estimation initiale de 5 000 kg :

```python
fuel_estimate_kg = 5_000.0
for _ in range(4):
    w_initial_kg = oew + payload_kg + phase_fuel_kg + fuel_estimate_kg
    breguet_exp = (distance_m * TSFC) / (aircraft.ld_ratio * speed_m_s)
    trip_fuel_kg = w_initial_kg * (1 - math.exp(-breguet_exp))
    fuel_estimate_kg = trip_fuel_kg
```

Le payload est calculé différemment selon le type d'appareil :
- **Passagers** : `nombre de sièges × 95 kg` (passager + bagage cabine)
- **Cargo** : `100 000 kg` fixe

**3. Total avec réserve réglementaire**

Le fuel total chargé intègre une réserve de 15 % conforme aux standards ICAO, et est plafonné à la capacité maximale des réservoirs :

```python
total_fuel_kg = min(
    (trip_fuel_kg + phase_fuel_kg) * (1 + RESERVE_RATIO),
    aircraft.max_fuel_kg,
)
```

### Paramètres requis dans `aircrafts.json`

Pour que le calcul fonctionne, chaque avion doit exposer les champs suivants dans sa configuration :

| Champ | Description |
|---|---|
| `operating_empty_weight_kg` | Masse à vide opérationnelle (OEW) |
| `ld_ratio` | Finesse aérodynamique (portance / traînée) |
| `cruising_speed` | Vitesse de croisière en km/h |
| `max_fuel_kg` | Capacité maximale des réservoirs |
| `passengers` | Nombre de sièges (ignoré si cargo) |
| `BASE_FUEL_FLOW` | Débits fixes par phase (`lineup`, `takeoff`, `climb`, `cruise`, `descent`, `landing`, `taxi`) |
| `fuel_flow_cruise_kg_per_s` | Débit croisière réel (utilisé comme `burn_rate` si > 0) |

---

## Navigation par waypoints et vitesse de décrochage

### Navigation waypoint par waypoint

Chaque corridor aérien définit une liste ordonnée de waypoints. Au lieu de tracer une ligne directe entre les deux aéroports, le vol progresse **de waypoint en waypoint** :

| Phase | Comportement |
|---|---|
| `TAKEOFF` | `dest` = premier waypoint du corridor, `current_waypoint_index = 0` |
| `CLIMBING` | Montée progressive vers l'altitude cible du waypoint[0] |
| `CRUISE` | Navigation séquentielle : waypoint[0] → waypoint[1] → … → waypoint[n-1] → aéroport d'arrivée |
| `DESCENDING` | Descente progressive vers 0 m, déclenchée uniquement après l'aéroport d'arrivée |

Le champ `current_waypoint_index` sur `Flight` trace la progression. Quand `index == len(waypoints)`, le vol est sur le **leg final** vers l'aéroport ; l'altitude reste stable à celle du dernier waypoint jusqu'au passage en `DESCENDING`.

Chaque waypoint définit une plage d'altitude autorisée (`min_alt_ft` / `max_alt_ft`). L'altitude cible est le milieu de cette plage :

```python
target_alt_m = (waypoint.min_alt_ft + waypoint.max_alt_ft) / 2 * 0.3048
```

La transition d'altitude entre waypoints est **progressive**, limitée par le taux de montée de l'appareil (`base_rate_of_climb_ft_per_min`).

### Calcul de v_stall selon l'altitude

La vitesse minimale de décrochage dépend de la densité de l'air, qui diminue avec l'altitude. À chaque tick en `CRUISE` et `CLIMBING`, ρ est recalculée via le **modèle ISA standard** :

```python
rho = 1.225 * max(0.0, (1 - 2.2558e-5 * altitude_m)) ** 4.2561
```

Puis la v_stall est dérivée de l'équation d'équilibre aérodynamique :

```python
v_stall = sqrt((2 * mass_kg * g) / (rho * wing_area_m2 * CL_max))
```

La vitesse de croisière effective est ensuite contrainte à `max(aircraft.cruising_speed, v_stall * 1.3)`, garantissant une marge de sécurité de 30 % au-dessus du décrochage à toute altitude.

Le coefficient `CL_max` (portance maximale en configuration clean) est stocké sur `Flight` (valeur par défaut : `1.4`).

---

Chaque runway maintient une liste `scheduled_flights` qui joue le rôle de **file de priorité ordonnée**.

- **Au départ**, les vols sont ajoutés à la runway assignée lors de leur création. La liste est ensuite triée par priorité (`FlightPriority.order`) puis par heure de départ estimée. Seul le premier vol de la file a le droit de passer en `LINEUP`, puis `TAKEOFF`. Les suivants attendent leur tour.
- **À l'arrivée**, les vols en descente sont ajoutés à la runway d'arrivée et triés par heure d'arrivée estimée. La runway d'arrivée est assignée dynamiquement pendant la phase de croisière, en choisissant la runway ayant le moins de vols déjà programmés.

Cette structure permet de simuler simplement la séquence de décollage/atterrissage sans collision sur une même piste, tout en respectant les priorités (urgences médicales, carburant critique, etc.).

---

## Complexités volontairement négligées

Les points suivants ont été identifiés mais volontairement mis de côté pour maintenir une première version fonctionnelle :

- **Séparation de sécurité entre avions** : il n'y a pas de bulle de sécurité calculée en vol. Deux avions peuvent théoriquement se croiser au même point géographique.
- **Capacité des runways en simultané** : une runway est marquée `OCCUPIED` pendant le décollage/atterrissage, mais la file d'attente ne tient pas compte des délais de dégagement réels.
- **Variation de consommation intra-phase** : `fuel_burn_rate_kg_per_s` est calculé au boarding et reflète le régime de croisière. Les facteurs par phase (`_FUEL_PHASE_FACTOR`) permettent de moduler la consommation, mais les micro-variations liées à la météo ou aux changements d'altitude entre waypoints ne sont pas modélisées.

---

## Reste à développer

### Conflits de trafic
Détecter et résoudre les conflits entre vols partageant le même corridor ou les mêmes waypoints. Implémenter une logique de séparation horizontale et verticale (niveaux de vol), et des manœuvres d'évitement.

### Incidents météorologiques
Modéliser des zones de turbulences, d'orages ou de restrictions d'espace aérien affectant dynamiquement les corridors. Un corridor pourrait passer en status `RESTRICTED` ou `CLOSED` en cours de simulation, forçant les vols à se rediriger.

### Fermeture de waypoints
Lorsqu'un waypoint est fermé (`WaypointStatus.CLOSED`), les vols devant le traverser doivent recalculer leur route. C'est ici que l'algorithme A* sur le graphe de waypoints prend tout son sens.

### Nœuds de taxiway bloqués
Un nœud du taxiway graph peut devenir indisponible (incident, véhicule, travaux). Le pathfinding A* doit alors recalculer un chemin alternatif en temps réel en excluant le nœud bloqué.

### Redirections en vol
Un vol en descente ou en croisière pourrait être redirigé vers un aéroport alternatif (déroutement) en cas d'impossibilité d'atterrissage (piste fermée, trafic saturé, météo). Le modèle `Flight` supporte déjà les champs nécessaires (`arrival_airport_code`, `dest_lat`, `dest_lon`).

### Consommation dynamique intra-phase
Le `fuel_burn_rate` varie déjà selon la phase (`_FUEL_PHASE_FACTOR`). Une amélioration possible serait d'affiner la consommation en fonction de l'altitude exacte à chaque tick et des gradients de montée/descente entre waypoints.

### Visualisation
Un adapter de visualisation est prévu (`adapter/`) pour chaque domaine. L'objectif est d'afficher en temps réel la grille de simulation (positions des avions, état des gates, flux sur les corridors, niveau de carburant) via **pygame** ou **matplotlib**, sans dépendance à un serveur externe.

---

## Structure du projet

```
AeroSim/
├── main/
│   ├── main.py
│   ├── flight/
│   │   ├── domain/          → Entité Flight, enums (FlightStatus, FlightPriority, RunwayUsageType)
│   │   ├── application/     → Services métier (physique, timing, factory, priorité)
│   │   └── adapter/         → (prévu : visualisation)
│   ├── aircraft/
│   │   ├── domain/          → Entité Aircraft, AircraftType
│   │   └── application/
│   ├── airline/
│   │   ├── domain/          → Entité Airline
│   │   └── application/
│   ├── airport/
│   │   ├── domain/          → Airport, Terminal, Gate, Runway, Node, Edge
│   │   ├── application/     → A* taxiway, assignation gates/runways
│   │   └── adapter/
│   ├── air_corridor/
│   │   ├── domain/          → AirCorridor, CorridorStatus, CorridorDirection
│   │   ├── application/     → Recherche de corridor disponible
│   │   └── adapter/
│   ├── waypoint/
│   │   ├── domain/          → Waypoint, WaypointStatus
│   │   └── application/
│   └── shared/
│       ├── bootstrap.py     → Chargement et initialisation du simulateur
│       ├── simulator.py     → Boucle de simulation principale
│       ├── simulator/
│       │   ├── departure_simulator/
│       │   │   ├── compute_fuel.py   → Calcul Breguet + phases sol
│       │   │   └── takeoff.py        → Décollage + initialisation navigation waypoints
│       │   ├── flight_simulator/
│       │   │   └── flight.py         → Tick CRUISE : navigation waypoints, v_stall, altitude ISA
│       │   └── landing_simulator/
│       │       ├── descent.py        → Déclenchement descente
│       │       └── landing.py        → Atterrissage et assignation gate
│       ├── object_factory.py → Hydratation JSON → objets domaine
│       ├── data_loader.py   → Lecture des fichiers JSON
│       └── init_logger.py   → Logs et affichage console
└── test/                    → À compléter
```

---

## Lancement

```bash
git clone https://github.com/alassane8/Air-Traffic-Simulator.git
pip install -r requirements.txt
pip install --upgrade -r requirements.txt
cd Air-Traffic-Simulator/main
python main.py
```