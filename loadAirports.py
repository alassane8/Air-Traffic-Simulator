import json

with open('airports.json', 'r') as airport_data:
        airports = json.load(airport_data)

        airports_names = airports[1]
        print(airports_names)





        airport_data.close()


print(airports)