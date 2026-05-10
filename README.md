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
