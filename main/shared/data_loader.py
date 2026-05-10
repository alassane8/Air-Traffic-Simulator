import json


def load_data(filename: str) -> dict:
    with open(filename, "r") as file:
        return json.load(file)
