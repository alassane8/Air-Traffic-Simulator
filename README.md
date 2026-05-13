# AeroSim

AeroSim est un simulateur de trafic aérien écrit en Python, conçu pour modéliser de manière réaliste le cycle de vie complet d'un vol, depuis l'assignation à une gate jusqu'à l'atterrissage et le retour à quai. Le projet est structuré selon une **architecture hexagonale** (Ports & Adapters), avec une séparation claire entre domaine, logique métier et infrastructure.

---

## Hypothèses du projet

Le simulateur repose sur plusieurs hypothèses de conception choisies pour maintenir un niveau de complexité gérable dans un premier temps afin de se concentrer sur l'orchestration des vols et l'attributions des pistes de décollage et d'atterrissage:

- **Un avion = un vol à la fois.** Un aéronef est assigné à une gate, génère un vol, décolle, atterrit, et redevient disponible. Il n'y a pas de rotation multi-étapes modélisée.
- **Les fichiers JSON sont la source de vérité.** Tous les aéroports, avions, compagnies et corridors sont définis statiquement dans des fichiers de configuration. Il n'y a pas de base de données.
- **Le temps est accéléré via un `TIME_SCALE`.** Un tick de simulation correspond à `TICK_INTERVAL * TIME_SCALE` secondes simulées. Par défaut, `TIME_SCALE = 60`, ce qui signifie qu'une seconde réelle représente une minute simulée.
- **La physique de vol est simplifiée.** La position géographique est interpolée via la formule de Haversine sur un grand cercle. Il n'y a pas de simulation de forces aérodynamiques, de vent ou de turbulences.
- **Les corridors sont bidirectionnels par défaut.** Un corridor peut être parcouru dans les deux sens sauf indication contraire dans la configuration.
- **La priorité d'un vol est tirée aléatoirement** selon une distribution pondérée (84 % `NORMAL`, 10 % `DELAY`, etc.), reflétant la réalité statistique du trafic aérien.

---

## Fichiers de configuration

Toute la donnée du simulateur est externalisée dans des fichiers JSON. Aucune valeur métier n'est codée en dur dans le code.

```
AeroSim/main/
├── config/aircrafts.json         → Flotte d'avions (type, vitesse, capacité)
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

En vol, l'avion suit un corridor aérien qui contient une séquence ordonnée de waypoints géographiques. La progression entre waypoints est calculée via interpolation sur grand cercle (formule de Haversine), et la position est mise à jour à chaque tick en fonction de la vitesse de croisière et du temps restant jusqu'à l'arrivée estimée.

À terme, l'algorithme A* pourra être appliqué sur le graphe des waypoints pour calculer dynamiquement des routes alternatives en cas de fermeture de waypoint ou de conflit de trafic.

---

## `scheduled_flights` : file d'ordre de départ et d'arrivée

Chaque runway maintient une liste `scheduled_flights` qui joue le rôle de **file de priorité ordonnée**.

- **Au départ**, les vols sont ajoutés à la runway assignée lors de leur création. La liste est ensuite triée par priorité (`FlightPriority.order`) puis par heure de départ estimée. Seul le premier vol de la file a le droit de passer en `LINEUP`, puis `TAKEOFF`. Les suivants attendent leur tour.
- **À l'arrivée**, les vols en descente sont ajoutés à la runway d'arrivée et triés par heure d'arrivée estimée. La runway d'arrivée est assignée dynamiquement pendant la phase de croisière, en choisissant la runway ayant le moins de vols déjà programmés.

Cette structure permet de simuler simplement la séquence de décollage/atterrissage sans collision sur une même piste, tout en respectant les priorités (urgences médicales, carburant critique, etc.).

---

## Complexités volontairement négligées

Les points suivants ont été identifiés mais volontairement mis de côté pour maintenir une première version fonctionnelle :

- **Séparation de sécurité entre avions** : il n'y a pas de bulle de sécurité calculée en vol. Deux avions peuvent théoriquement se croiser au même point géographique.
- **Capacité des runways en simultané** : une runway est marquée `OCCUPIED` pendant le décollage/atterrissage, mais la file d'attente ne tient pas compte des délais de dégagement réels.
- **Consommation de carburant différenciée** : le champ `fuel_burn_rate_kg_per_s` existe dans le modèle `Flight` mais n'est pas encore calculé dynamiquement selon le type d'avion, la phase de vol ou la météo.
- **Poids de l'avion** : le modèle `Aircraft` ne tient pas compte du poids au décollage (MTOW), ce qui simplifiait la sélection de runway (une narrow peut en théorie utiliser une courte piste, une large non).

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

### Impact du poids sur la vitesse et la sélection de runway
La masse de l'avion au décollage (passagers + carburant + fret) devrait impacter la vitesse de montée, la distance de roulage nécessaire, et donc la sélection de runway. Un avion lourd nécessite une piste plus longue et aura une phase de montée plus lente.

### Visualisation
Un adapter de visualisation est prévu (`adapter/`) pour chaque domaine. L'objectif est d'afficher en temps réel la grille de simulation (positions des avions, état des gates, flux sur les corridors) via **pygame** ou **matplotlib**, sans dépendance à un serveur externe.

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
│       ├── object_factory.py → Hydratation JSON → objets domaine
│       ├── data_loader.py   → Lecture des fichiers JSON
│       └── init_logger.py   → Logs et affichage console
└── test/                    → À compléter
```

---

## Lancement

```bash
git clone <url_du_repo>
pip install -r requirements.txt
pip install --upgrade -r requirements.txt
cd AeroSim/main
python main.py
```