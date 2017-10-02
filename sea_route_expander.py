import requests
import sys
from time import sleep
import csv
import json
import codecs
from simplify import simplify


def get(url_base, payload):
    r = requests.get(url_base, params=payload)
    print(r.request.url)
    return r.json()


routes = {}
data_files = []

if len(sys.argv) > 1:
    data_files.append(sys.argv[1])
else:
    for i in range(9):
        data_files.append('data' + str(i+1) + '.csv')

for data_file in data_files:
    stops = []

    with open(data_file, newline='') as f:
        reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE)
        for row in reader:
            stops.append(row)

    for i in range(len(stops)-1):
        A = stops[i]
        B = stops[i+1]

        from_lat, from_lon = A['latitude'], A['longitude']
        to_lat, to_lon = B['latitude'], B['longitude']

        route_name = str(
            '{:.5f}'.format(float(from_lat)) + ':'
            + '{:.5f}'.format(float(from_lon)) + ':'
            + '{:.5f}'.format(float(to_lat)) + ':'
            + '{:.5f}'.format(float(to_lon))
        )

        url_base = str(

            codecs.encode(
                'uggcf://jjj.frnebhgrf.pbz/qrsnhyg-freivpr/ebhgr',
                'rot-13'  # safety first
            )
            + '/lon:' + str(from_lon) + 'lat:' + str(from_lat)
            + '/lon:' + str(to_lon) + 'lat:' + str(to_lat)
        )

        payload = {
            'speed': '10',
            'transshipmentFactor': '10',
            'streetFactor': '5',
            'avoidedTwCountriesCsv': '',
            'avoidInland': 'false',
            'unblockedAreasCsv': '',
            'blockedAreasCsv': '23,11,35,13,17',
            'type': 'graph',
            'multiRoute': 'false'
        }

        try:
            sleep(3)
            rj = get(url_base, payload)
            routes[route_name] = rj['getRouteJson']
        except:
            print("FAILED")
            payload['multiRoute'] = 'true'
            sleep(3)
            rj = get(url_base, payload)
            if rj.get('getRouteJson'):
                routes[route_name] = rj['getRouteJson']
            else:
                print("FAILED!!!")

#        print(routes[route_name])

with open('all_routes.json', 'w') as outfile:
    json.dump(routes, outfile, sort_keys=True)

# Now compact to just the essential bits
with open('all_routes.json', 'r') as jfile:
    jf = json.load(jfile)

new_data = {}

for index, data in sorted(jf.items()):
    new_route = []
    route_time = 0
    if isinstance(data, list):
        for segment in data:
            route_time += segment['journeytime']
            segpts = segment['routepoints']
            route = [{'lat': pt['lat'], 'lng': pt['lon']} for pt in segpts]
            new_route += route

        if len(new_route) > 0:
            new_data[index] = {'time': route_time, 'route': new_route}

with open('compact_routes.json', 'w') as ofile:
    json.dump(new_data, ofile)


# Now simplify the routes

with open('compact_routes.json', 'r') as f:
    crj = json.load(f)

new_routes = {}

for identifier, route in crj.items():
    new_route = simplify(route['route'], tolerance=0.05)

    print(
        len(route['route']), '->', len(new_route)
    )

    route['route'] = new_route

with open('simplified_routes.json', 'w') as of:
    of.write('var simplified_routes = ')
    json.dump(crj, of, indent='  ')
    of.write(';')