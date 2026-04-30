import json

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def loadAirportsData() -> dict:
    with open('airports.json', 'r') as file:
        airports = json.load(file)
    return airports

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def loadAircraftData() -> dict:
    with open('aircrafts.json', 'r') as file:
        aircrafts = json.load(file)
    return aircrafts