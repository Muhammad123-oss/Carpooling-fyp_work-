import folium
import geopy
import numpy as np
import pandas as pd
import requests
import pymysql
import json


def dbconnect():
    # database connection
    connection = pymysql.connect(host="localhost", user="root", passwd="", database="carpooling")
    # cursor = connection.cursor()
    # some other statements  with the help of cursor
    return connection
def get_directions_response(lat1, long1, lat2, long2, mode='drive'):
    url = "https://route-and-directions.p.rapidapi.com/v1/routing"
    querystring = {"waypoints": f"{str(lat1)},{str(long1)}|{str(lat2)},{str(long2)}", "mode": "drive"}
    headers = {
        "X-RapidAPI-Key": "889d5281acmsh9a8b0e8a6bdfce3p188328jsna791960c7d91",
        "X-RapidAPI-Host": "route-and-directions.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    return response
def create_map(response):
    # use the response
    mls = response.json()['features'][0]['geometry']['coordinates']
    points = [(i[1], i[0]) for i in mls[0]]
    m = folium.Map()

    # add marker for the start and ending points
    for point in [points[0], points[-1]]:
        folium.Marker(point).add_to(m)
    # add the lines
    folium.PolyLine(points, weight=5, opacity=1).add_to(m)
    # create optimal zoom
    df = pd.DataFrame(mls[0]).rename(columns={0: 'Lon', 1: 'Lat'})[['Lat', 'Lon']]
    sw = df[['Lat', 'Lon']].min().values.tolist()
    ne = df[['Lat', 'Lon']].max().values.tolist()
    m.fit_bounds([sw, ne])
    return m
def cordinate_to_name(lat,long):
    url = "https://trueway-geocoding.p.rapidapi.com/ReverseGeocode"
    querystring = {"location": f"{str(lat)},{str(long)}", "language": "en"}
    headers = {
        "X-RapidAPI-Key": "889d5281acmsh9a8b0e8a6bdfce3p188328jsna791960c7d91",
        "X-RapidAPI-Host": "trueway-geocoding.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    return response.json()
    #print(response.text)



# Main
# response = get_directions_response(48.34364,10.87474,48.37073,10.909257)
# response = get_directions_response(24.8904, 67.0911,24.7794, 67.0908)


# fast to halt
response = get_directions_response( 24.902885, 67.197578,24.8846, 67.1754)

m = create_map(response)
m.save('./route_map.html')


routeArray =[]
coo=[]
total_cood=len(response.json()['features'][0]['geometry']['coordinates'][0])
#gap=total_cood/5
# print(int(gap))
for y in response.json()['features'][0]['geometry']['coordinates'][0]:        #[::int(gap)]:
    coo.append([y[1],y[0]])


# setting up database
connection=dbconnect()
cursor=connection.cursor()
routeee=json.dumps(coo)
# print(routeee)
mySql_insert_query ="""INSERT INTO `routes`(`name`, `s_location_point`, `d_location_point`)
VALUES (?, geography::ST_GeomFromText('POINT(0.18000 0.36000)', 4326), geography::ST_GeomFromText('POINT(0.18021 0.360321)', 4326))"""
route_name="Airport to tower"
starting_point="'POINT(0.18000 0.36000)'"
dest_point= "'POINT(0.18021 0.360321)'"
record = (route_name,)
cursor.execute(mySql_insert_query,record)
connection.commit()

# reading file
# cursor.execute("select croute from routes")
# record=cursor.fetchall()

# for row in record:
#     # print(json.loads(row))
#     r1=np.asarray(row)
#     print(r1[0])

#     print('\n')

# print(routeArray)
# result=cordinate_to_name(24.8961, 67.0814)
# for x in result['results']:
#     if(x['location_type']=='exact'):
#         print(x['sublocality'])