# ✈️ AeroSim — Moteur de Simulation du Trafic Aérien

> Moteur de simulation en Python modélisant l'infrastructure aéroportuaire, la prise de décision du contrôle aérien (ATC) et la résolution de conflits de trajectoires en temps réel.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Statut](https://img.shields.io/badge/Statut-En%20développement-orange?style=flat)
![Licence](https://img.shields.io/badge/Licence-MIT-green?style=flat)
![Domaine](https://img.shields.io/badge/Domaine-Aérospatial%20%7C%20Simulation-0D1B2A?style=flat)

---

## 📌 Présentation

**AeroSim** simule le cycle de vie complet du trafic aérien autour d'un aéroport majeur — de la planification des vols et l'attribution des pistes jusqu'à la détection de conflits en temps réel et la prise de décision du contrôleur aérien (ATC).

Le projet s'inspire des systèmes utilisés par **Eurocontrol**, **Thales Air Systems** et le **CNES** (Centre National d'Études Spatiales), où les moteurs de simulation sont des outils critiques pour valider les algorithmes de gestion du trafic aérien (ATM) avant leur déploiement opérationnel.

La simulation est construite autour des aéroports **Charles de Gaulle (CDG)** et **Paris-Orly (ORY)**, en utilisant des données d'infrastructure réelles (longueurs de pistes, caps magnétiques, capacités des terminaux) issues d'OurAirports et de la documentation OACI.

---

## 🎯 Objectifs

- Modéliser l'infrastructure physique d'un aéroport (pistes, terminaux, portes) à partir de fichiers de configuration structurés
- Simuler le cycle de vie complet d'un vol : `PLANIFIÉ → EMBARQUEMENT → ROULAGE → DÉCOLLAGE → CROISIÈRE → APPROCHE → ATTERRISSAGE`
- Implémenter un contrôleur ATC appliquant les règles de séparation OACI et l'attribution des pistes par priorité
- Détecter et résoudre les conflits de trajectoires via des algorithmes géométriques vectoriels
- Visualiser le trafic en direct sur une carte interactive avec des métriques en temps réel
- Comparer plusieurs stratégies d'ordonnancement (FCFS, priorité, heuristiques optimisées)

---

## 🏗️ Architecture

AeroSim suit une **architecture hexagonale** stricte (Ports & Adaptateurs). Le domaine est totalement isolé des préoccupations d'infrastructure — il n'a aucune connaissance des fichiers JSON, des dashboards ou des APIs externes. Toute communication passe par des ports (interfaces) implémentés par des adaptateurs.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ADAPTATEURS PILOTANTS                          │
│              (ils appellent l'application — côté gauche)            │
│                                                                     │
│   ┌─────────────────┐          ┌───────────────────┐                │
│   │   CLI Runner    │          │  Dashboard Dash   │                │
│   │  simulator.py   │          │  dashboard.py     │                │
│   └────────┬────────┘          └────────┬──────────┘                │
│            │                            │                           │
└────────────┼────────────────────────────┼───────────────────────────┘
             │  appelle via               │  lit via
             ▼  ISimulationPort           ▼  IMetricsPort
┌─────────────────────────────────────────────────────────────────────┐
│                        COUCHE APPLICATION                           │
│                    (cas d'usage / services)                         │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    SimulationService                         │  │
│   │   ┌─────────────────┐  ┌───────────────┐  ┌──────────────┐   │  │
│   │   │  ATCController  │  │   Scheduler   │  │ConflictSolver│   │  │
│   │   │  atc_controller │  │  scheduler.py │  │conflict_     │   │  │
│   │   │      .py        │  │               │  │solver.py     │   │  │
│   │   └────────┬────────┘  └───────┬───────┘  └──────┬───────┘   │  │
│   └────────────┼───────────────────┼─────────────────┼───────────┘  │
│                │    opère sur      │                 │              │
└────────────────┼───────────────────┼─────────────────┼──────────────┘
                 ▼                   ▼                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                          COUCHE DOMAINE                            │
│           (logique métier pure — aucune dépendance externe)        │
│                                                                    │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│   │ Airport  │  │  Runway  │  │   Gate   │  │    Aircraft      │   │
│   │airport.py│  │runway.py │  │  gate.py │  │  aircraft.py     │   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                                    │
│   ┌──────────────────────┐    ┌─────────────────────────────────┐  │
│   │      Terminal        │    │          SimState               │  │
│   │    terminal.py       │    │          state.py               │  │
│   └──────────────────────┘    └─────────────────────────────────┘  │
│                                                                    │
│         ┌──────────────────────────────────────┐                   │
│         │               PORTS                  │                   │
│         │  IAirportRepository  IEventLogger    │                   │
│         │  IFlightDataSource   IMetricsPort    │                   │
│         └──────────────────────────────────────┘                   │
└────────────────────────────────────────────────────────────────────┘
                 ▲                   ▲                  ▲
                 │  implémente       │                  │
┌────────────────┼───────────────────┼──────────────────┼────────────┐
│                       ADAPTATEURS PILOTÉS                          │
│              (appelés par le domaine — côté droit)                 │
│                                                                    │
│   ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│   │  JsonAirport    │  │  CsvEventLogger  │  │ OpenSkyAdapter   │  │
│   │  Repository     │  │  logger.py       │  │ opensky.py       │  │
│   │  loader.py      │  │                  │  │                  │  │
│   └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│            │                    │                     │            │
└────────────┼────────────────────┼─────────────────────┼────────────┘
             ▼                    ▼                     ▼
      airports.json          events.csv           API OpenSky
      aircrafts.json         simulation.db        (ADS-B live)
```

### Structure du projet

```
aerosim/
│
├── domain/                         # ● DOMAINE — aucune dépendance externe
│   ├── models/
│   │   ├── airport.py
│   │   ├── terminal.py
│   │   ├── runway.py
│   │   ├── gate.py
│   │   └── aircraft.py
│   ├── services/
│   │   ├── atc_controller.py       # Logique ATC : séquençage, priorité, séparation
│   │   ├── scheduler.py            # Gestion de la file des vols
│   │   └── conflict_solver.py      # Détection et résolution de conflits géométriques
│   ├── state.py                    # État de la simulation en mémoire
│   └── ports/                      # Interfaces (classes abstraites)
│       ├── airport_repository.py   # IAirportRepository
│       ├── event_logger.py         # IEventLogger
│       ├── flight_data_source.py   # IFlightDataSource
│       └── metrics_port.py         # IMetricsPort
│
├── application/                    # ● APPLICATION — orchestre les cas d'usage
│   └── simulation_service.py       # Boucle principale, appelle les services domaine
│
├── adapters/                       # ● ADAPTATEURS — implémentent les ports
│   ├── driving/
│   │   ├── cli/
│   │   │   └── simulator.py        # Point d'entrée : python -m aerosim
│   │   └── dashboard/
│   │       ├── dashboard.py        # Interface Plotly Dash
│   │       └── map_view.py         # Carte de trajectoires Folium
│   └── driven/
│       ├── persistence/
│       │   ├── json_airport_repo.py  # Lecture airports.json → objets domaine
│       │   └── csv_event_logger.py   # Écriture events.csv
│       └── external/
│           └── opensky_adapter.py    # API OpenSky Network → vols domaine
│
├── data/
│   ├── airports.json               # Configuration statique (CDG, ORY)
│   └── aircrafts.json              # Définitions de la flotte d'appareils
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

### Principe clé de l'architecture hexagonale

Le domaine **n'importe jamais** depuis `adapters/` ou `data/`. Les flèches de dépendance pointent toujours **vers l'intérieur**, en direction du domaine. Cela signifie que l'ensemble du moteur de simulation peut être testé sans aucune I/O fichier, API externe ou interface graphique — uniquement des objets Python purs.

```python
# ✅ correct — le domaine définit l'interface
class IAirportRepository(ABC):
    @abstractmethod
    def load_all(self) -> List[Airport]: ...

# ✅ correct — l'adaptateur l'implémente
class JsonAirportRepository(IAirportRepository):
    def load_all(self) -> List[Airport]:
        # lit airports.json, retourne des objets domaine
        ...

# ❌ interdit — le domaine ne doit pas savoir que le JSON existe
class ATCController:
    def __init__(self):
        with open("airports.json") as f:  # violation
            ...
```

---

## ⚙️ Concepts fondamentaux

### Infrastructure aéroportuaire

La configuration de l'aéroport est chargée une seule fois au démarrage depuis `airports.json`. Tout l'état dynamique (occupation des pistes, disponibilité des portes, charge des terminaux) vit exclusivement en mémoire pendant la simulation — jamais réécrit dans le fichier de configuration.

```python
@dataclass
class Runway:
    id: str
    length: float       # mètres
    heading: int        # cap magnétique (0–360°)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    # --- état dynamique (jamais dans le JSON) ---
    status: str = "FREE"               # FREE | OCCUPIED | CLOSED | MAINTENANCE
    current_aircraft: Optional[str] = None
```

### Contrôleur ATC

Le contrôleur ATC applique les règles de séparation de l'**OACI Doc 4444** :

- Séparation minimale entre deux appareils successifs sur une même piste : **90 secondes**
- File de priorité : `URGENCE > CARBURANT_CRITIQUE > MÉDICAL > RETARD > NORMAL`
- Attribution de piste selon le vent et les performances de l'appareil
- Gestion des hippodromes d'attente lorsque la capacité de l'espace aérien terminal (TMA) est atteinte

### Détection de conflits

Les trajectoires sont modélisées comme des vecteurs paramétriques. Le solveur de conflits projette les positions N pas de temps en avant et signale les paires d'appareils violant les minimums OACI :

- Séparation latérale : **3 NM (5,5 km)**
- Séparation verticale : **1 000 ft (300 m)**

Stratégies de résolution : ajustement de vitesse, manœuvre de cap, ou assignation d'un hippodrome d'attente.

---

## 🚀 Démarrage rapide

### Prérequis

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/your-username/aerosim.git
cd aerosim
pip install -r requirements.txt
```

### Lancer la simulation

```bash
python -m simulation.simulator
```

### Lancer le dashboard

```bash
python -m visualization.dashboard
# Ouvrir http://localhost:8050
```

### Lancer les tests

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## 📦 Stack technique

| Catégorie | Librairie | Usage |
|---|---|---|
| Cœur | Python 3.11, dataclasses | Modélisation du domaine |
| Calcul numérique | NumPy | Calculs vectoriels, géométrie des trajectoires |
| Géométrie | Shapely | Détection de conflits spatiaux 2D |
| Données | Pandas | Analyse des logs, calcul des métriques |
| Visualisation | Plotly + Dash | Dashboard interactif temps réel |
| Cartographie | Folium | Rendu des trajectoires sur fond de carte réel |
| Données réelles | API OpenSky Network | Positions de vols ADS-B en direct |
| Tests | pytest, pytest-cov | Tests unitaires et d'intégration |
| Logging | Loguru | Journalisation structurée des événements |
| Configuration | Pydantic | Validation des données au chargement JSON |

---

## 📊 Métriques de simulation

Le moteur calcule et expose les KPIs suivants, comparables entre stratégies d'ordonnancement :

| Métrique | Description |
|---|---|
| **Débit** | Nombre de vols traités par heure simulée |
| **Retard moyen** | Heure d'atterrissage réelle vs ETA planifiée |
| **Taux d'utilisation des pistes** | % du temps où chaque piste est occupée |
| **Taux de conflits** | Conflits détectés pour 100 vols |
| **Taux de résolution** | % de conflits résolus sans intervention humaine |

---

## 🗺️ Feuille de route

- [x] Modèles d'infrastructure aéroportuaire (Runway, Gate, Terminal, Airport)
- [x] Chargeur de configuration JSON
- [ ] Modèle d'appareil et cycle de vie d'un vol
- [ ] Contrôleur ATC avec règles de séparation OACI
- [ ] Planificateur de vols par priorité
- [ ] Détection de conflits géométrique (2D)
- [ ] Résolution de conflits (ajustement vitesse + cap)
- [ ] Dashboard Plotly Dash temps réel
- [ ] Intégration OpenSky Network (données de vols réels)
- [ ] Détection de conflits 3D (couche altitude)
- [ ] Benchmark des stratégies (FCFS vs heuristique optimisée)
- [ ] Rapport technique + article publié

---

## 🔗 Pertinence industrielle

Ce projet adresse directement des défis techniques présents dans les systèmes aérospatial opérationnels :

- **Eurocontrol** — Le réseau ATM européen utilise des moteurs de simulation pour valider les algorithmes de séparation avant déploiement en conditions réelles
- **Thales Air Systems** — Développe des outils d'aide à la décision ATC pour les grands aéroports internationaux
- **CNES** — Applique une modélisation de trajectoires et une logique d'évitement de collision similaires à la mécanique orbitale et à l'évitement de collision satellitaire
- **DSNA** (Direction des Services de la Navigation Aérienne) — Autorité française du contrôle aérien civil, utilise la simulation pour la formation des contrôleurs

Le vocabulaire du domaine employé dans ce projet (ADS-B, TMA, TCAS, OACI Doc 4444, minima de séparation) est conforme aux standards de l'ingénierie aérospatiale professionnelle.

---

## 📚 Références et sources de données

- [OACI Doc 4444](https://www.icao.int) — PANS-ATM : Procédures pour les services de navigation aérienne
- [OpenSky Network](https://opensky-network.org) — API de données de vols ADS-B gratuites et historiques
- [OurAirports](https://ourairports.com) — Base de données ouverte des aéroports et pistes (CSV)
- [BlueSky ATC Simulator](https://github.com/TUDelft-CNS-ATM/bluesky) — Simulateur de référence open-source (TU Delft)
- [Eurocontrol BADA](https://www.eurocontrol.int/model/bada) — Base de données des performances aéronefs

---

## 👤 Auteur

**Alassane WADE**
Ingénieur Développement Fullstack — Paris, France
Spécialisé dans les systèmes géospatiaux, la simulation et le logiciel aérospatial appliqué.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Alassane%20Wade-0077B5?style=flat&logo=linkedin)](https://linkedin.com/in/alassane-wade)
[![GitHub](https://img.shields.io/badge/GitHub-alassane8-181717?style=flat&logo=github)](https://github.com/alassane8)

