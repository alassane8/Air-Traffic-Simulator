from json.tool import main
import loadData
import createObjects
import initLogs 
import time

def main() -> int:
    initLogs.log(">>> BOOT SEQUENCE INITIATED...", 0.04)
    time.sleep(0.8)

    initLogs.phase("Chargement des modules de données")

    initLogs.loading("Récupération des données aéronautiques")
    aircraftsData = loadData.loadAircraftData()
    initLogs.success("Données avions chargées")

    initLogs.loading("Récupération des infrastructures aéroportuaires")
    airportsData = loadData.loadAirportsData()
    initLogs.success("Données aéroports chargées")

    initLogs.phase("Construction des objets système")

    initLogs.loading("Assemblage des unités aériennes")
    aircrafts = createObjects.createAircrafts(aircraftsData)
    initLogs.success(f"{len(aircrafts)} appareils opérationnels")

    initLogs.loading("Initialisation des hubs aéroportuaires")
    airports = createObjects.createAirports(airportsData)
    initLogs.success(f"{len(airports)} aéroports en ligne")

    initLogs.loading("Déploiement des terminaux")
    terminals = createObjects.createTerminals(airportsData)
    initLogs.success(f"{len(terminals)} terminaux actifs")

    initLogs.loading("Activation des portes d’embarquement")
    gates = createObjects.createGates(airportsData)
    initLogs.success(f"{len(gates)} portes prêtes")

    initLogs.loading("Synchronisation des pistes")
    runways = createObjects.createRunways(airportsData)
    initLogs.success(f"{len(runways)} pistes opérationnelles")

    initLogs.phase("Système prêt")

    initLogs.log(">>> ALL SYSTEMS NOMINAL", 0.04)
    time.sleep(0.5)
    initLogs.log(">>> READY FOR DEPLOYMENT", 0.04)

    return 0


if __name__ == '__main__':
    main()