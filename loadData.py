import json

def loadData(filename: str) -> dict:
    with open(filename, 'r') as file:
        return json.load(file)