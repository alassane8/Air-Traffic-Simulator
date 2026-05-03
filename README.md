# AeroSim — Simulateur de Trafic Aérien
 
> Modélisation d'un simulateur de trafic aérien implémentant des aéroports, leurs terminaux, portes, pistes d'atterrissage et de décollage.
 
---
 
## Présentation
 
**AeroSim** simule le cycle de vie complet du trafic aérien — de la planification des vols et l'attribution des pistes jusqu'à la détection de conflits en temps réel et la prise de décision du contrôleur aérien (ATC).
 
Le projet s'inspire des systèmes utilisés par **Eurocontrol**, **Thales Air Systems** et le **CNES** (Centre National d'Études Spatiales), où les moteurs de simulation sont des outils critiques pour valider les algorithmes de gestion du trafic aérien (ATM) avant leur déploiement opérationnel.
 
La simulation est construite autour de fichiers de configuration qui permettent de modéliser les aéroports, les avions, les couloirs aériens et les compagnies aériennes en utilisant des données d'infrastructure réelles (longueurs de pistes, caps magnétiques, capacités des terminaux) issues d'**OurAirports** et de la documentation **OACI**.
 
---
 
## Objectifs
 
- Modéliser l'infrastructure physique d'un aéroport (pistes, terminaux, portes, couloirs aériens, compagnies aériennes) à partir de fichiers de configuration structurés
- Simuler le cycle de vie complet d'un vol : `PLANIFIÉ → EMBARQUEMENT → ROULAGE → DÉCOLLAGE → CROISIÈRE → APPROCHE → ATTERRISSAGE`
- Implémenter un contrôleur ATC appliquant les règles de séparation OACI et l'attribution des pistes par priorité
- Visualiser le trafic en direct sur une carte interactive avec des métriques en temps réel
---
 
## Démarrage rapide
 
### Prérequis
 
- Python 3.11+
- pip
### Installation
 
```bash
git clone https://github.com/alassane8/AeroSim.git
cd AeroSim
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
 
## Architecture & Fonctionnement
 
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
 
### Hypothèses du projet
 
Plusieurs hypothèses ont été émises afin de simplifier certains traitements au sein du simulateur :
 
- La vitesse des avions dans les couloirs aériens correspond initialement à leur vitesse de croisière
- Les phases de décollage et d'atterrissage sont modélisées de manière temporelle et n'appartiennent pas aux couloirs aériens
- Le nombre de passagers d'un vol, la position initiale des avions dans les portes des terminaux et les compagnies aériennes associées au vol sont déterminés de manière aléatoire
- Une porte peut accueillir uniquement un avion
---
 
## Stack technique
 
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
 
## Métriques de simulation
 
Le moteur calcule et expose les KPIs suivants, comparables entre stratégies d'ordonnancement :
 
| Métrique | Description |
|---|---|
| **Débit** | Nombre de vols traités par heure simulée |
| **Retard moyen** | Heure d'atterrissage réelle vs ETA planifiée |
| **Taux d'utilisation des pistes** | % du temps où chaque piste est occupée |
| **Taux de conflits** | Conflits détectés pour 100 vols |
| **Taux de résolution** | % de conflits résolus sans intervention humaine |
 
---
 
## Feuille de route
 
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
 
## Pertinence industrielle
 
Ce projet adresse directement des défis techniques présents dans les systèmes aérospaciaux opérationnels :
 
- **Eurocontrol** — Le réseau ATM européen utilise des moteurs de simulation pour valider les algorithmes de séparation avant déploiement en conditions réelles
- **Thales Air Systems** — Développe des outils d'aide à la décision ATC pour les grands aéroports internationaux
- **CNES** — Applique une modélisation de trajectoires et une logique d'évitement de collision similaires à la mécanique orbitale et à l'évitement de collision satellitaire
- **DSNA** (Direction des Services de la Navigation Aérienne) — Autorité française du contrôle aérien civil, utilise la simulation pour la formation des contrôleurs
> Le vocabulaire du domaine employé dans ce projet (ADS-B, TMA, TCAS, OACI Doc 4444, minima de séparation) est conforme aux standards de l'ingénierie aérospatiale professionnelle.
 
---
 
## Références et sources de données
 
- [OACI Doc 4444](https://www.icao.int/) — PANS-ATM : Procédures pour les services de navigation aérienne
- [OpenSky Network](https://opensky-network.org/) — API de données de vols ADS-B gratuites et historiques
- [OurAirports](https://ourairports.com/) — Base de données ouverte des aéroports et pistes (CSV)
- [BlueSky ATC Simulator](https://github.com/TUDelft-CNS-ATM/bluesky) — Simulateur de référence open-source (TU Delft)
- [Eurocontrol BADA](https://www.eurocontrol.int/model/bada) — Base de données des performances aéronefs
---
 
## Auteur
 
**Alassane Wade**