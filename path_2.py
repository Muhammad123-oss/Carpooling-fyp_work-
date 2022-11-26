import folium
import geopy
import numpy as np
import pandas as pd
import requests
import pymysql
import json
import http.client
import re
from math import radians, cos, sin, asin, sqrt


def dbconnect():
    # database connection
    connection = pymysql.connect(host="localhost", user="root", passwd="", database="carpooling")
    # cursor = connection.cursor()
    # some other statements  with the help of cursor
    return connection

    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
def find_dist_btw_point(src_lat,src_lon,dest_lat,dest_lon):
    """
    map(fun, iter)
    fun : It is a function to which map passes each element of given iterable.
    iter : It is a iterable which is to be mapped.
    """
    # Converting decimal degrees to radians
    src_lat,src_lon,dest_lat,dest_lon=map(radians,[src_lat,src_lon,dest_lat,dest_lon])
    dist_lat=dest_lat-src_lat
    dist_lon=dest_lon-src_lon
    a=sin(dist_lat/2)**2 + cos(src_lat) * cos(dest_lat) * sin(dist_lon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    R=6371
    return c*R

def locate_user(user_src_lat,user_src_long,user_dest_lat,user_dest_long):
    # Checking for similar destination routes (dest long lat ,source long lat)
    dest_data=get_same_route(user_dest_lat,user_dest_long)
    for row in dest_data:
        # print(json.loads(row))
        r1=np.asarray(row)
        #Converting json(string) column from DB to Python list
        arr_type=json.loads(r1[6])
        # print(r1[1])  
        print(len(arr_type))
        # print('\n')



def get_fare_info(vehicle):
    # Creating a Dictionary for vehicle fare info
    fare_info={
        'mini':{'base_fee':100.28,'per_km':17,'per_min':7.63,'min_fare':131},
        'go':{'base_fee':124.18,'per_km':21.06,'per_min':9.45,'min_fare':163}
    }
    return fare_info[vehicle]

# System Base Fare Caculation Based On Distance+Time
def sys_based_fare_price(result):
    distance_travel=result['rows'][0]['elements'][0]['distance']['value']/1000 #ERROR BCZ API WEEK LIMIT EXISTS
    time_taken=result['rows'][0]['elements'][0]['duration']['value']/60 #ERROR BCZ API WEEK LIMIT EXISTS
    # distance_travel=10 # I hardcoded as i have an error
    # time_taken=5 # I hardcoded as i have an error
    car_info=get_fare_info("mini")
    # print(time_taken)
    # print(car_info['base_fee'])
    fare=car_info['base_fee']+(car_info['per_min']*time_taken) + (car_info['per_km']*distance_travel)
    if(fare<car_info['min_fare']):
        return car_info['min_fare']
    else:
        return fare

# User Base Fare Caculation Based On Distance+Time
def user_based_fare_price(result):
    distance_travel=result['rows'][0]['elements'][0]['distance']['value']/1000 #ERROR BCZ API WEEK LIMIT EXISTS
    time_taken=result['rows'][0]['elements'][0]['duration']['value']/60 #ERROR BCZ API WEEK LIMIT EXISTS
    # distance_travel=10 # I hardcoded as i have an error
    # time_taken=5 # I hardcoded as i have an error
    fare_per_km=float(input("How much fare per km you want to charge: "))
    fare_per_min=float(input("How much fare per minute you want to charge: "))
    car_info=get_fare_info("mini")
    fare=car_info['base_fee']+(fare_per_min*time_taken)+(fare_per_km*distance_travel)
    return fare


# User Base Fare Caculation Based On Distance 
def user_based_fare_price_on_distance(result):
    distance_travel=result['rows'][0]['elements'][0]['distance']['value']/1000 #ERROR BCZ API WEEK LIMIT EXISTS
    # distance_travel=10 # I hardcoded as i have an error
    fare_per_km=float(input("How much fare per km you want to charge: "))
    car_info=get_fare_info("mini")
    fare=car_info['base_fee']+(fare_per_km*distance_travel)
    return fare


def get_distance_time():
    query={"origins":"24.878937747538565,67.1884669257004","destinations":"24.857142456865084,67.26475889871588","departure_time":"now","key":"ntTWUnz82Npcyzj2xFj0yT8vojEjJ"}
    response=requests.get("https://api.distancematrix.ai/maps/api/distancematrix/json",params=query)
    return response.json()
    # conn = http.client.HTTPSConnection("api.distancematrix.ai")
    # conn.request("GET", "/maps/api/distancematrix/json?origins=24.878937747538565%2C67.1884669257004&destinations=24.857142456865084%2C67.26475889871588&departure_time=now&key=ntTWUnz82Npcyzj2xFj0yT8vojEjJ")
    # res = conn.getresponse()
    # data = res.read()
    # return data

def get_same_route(des_lat,des_long):
    conn=dbconnect()
    # {des_lat:.6f}
    cursor=connection.cursor()
    # print(start_location)
    # SELECT * FROM `routes` where (((24.9085*10000) - CONVERT((slat*10000),INT)) <> 0);
    cursor.execute("SELECT * FROM `routes` where ((({des_lat:.6f}*1000000) - CONVERT((dlat*1000000),INT)) = 0)  AND \
        ((({des_long:.6f}*1000000) - CONVERT((dlong*1000000),INT)) = 0)"\
        .format(des_long=des_long,des_lat=des_lat))
    
    return cursor.fetchall()

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
response = get_directions_response( 24.908460648396446, 67.220800769881,24.848005654110313, 66.99520521035566)

m = create_map(response)
m.save('./route_map.html')


routeArray =[]
coo=[]
total_cood=len(response.json()['features'][0]['geometry']['coordinates'][0])
# print(total_cood)
#gap=total_cood/5
# print(int(gap))
for y in response.json()['features'][0]['geometry']['coordinates'][0]:        #[::int(gap)]:
    coo.append([y[1],y[0]])


# setting up database
connection=dbconnect()
cursor=connection.cursor()
routeee=json.dumps(coo)
# print(routeee)
# cursor.execute("INSERT INTO routes(name,slat,slong,dlat,dlong,croute) VALUES(%s,%s,%s,%s,%s,%s)",('r2',24.908460648396446, 67.220800769881,24.848005654110313, 66.99520521035566,routeee))

# No new table required if we are going for each row a route. Helpful when multiple route has same path
# cursor.execute("INSERT INTO routes(route_no,complete_route) VALUES(%s,%s)",(routeee))
# connection.commit()

# # Checking for similar destination routes (dest long lat ,source long lat)
# dest_data=get_same_route(24.848005, 66.995209)
# for row in dest_data:
#     # print(json.loads(row))
#     r1=np.asarray(row)
#     #Converting json(string) column from DB to Python list
#     arr_type=json.loads(r1[6])  
#     # print(len(arr_type))

#     # print('\n')

# reading file
cursor.execute("select croute from routes")
record=cursor.fetchall()

for row in record:
    # print(json.loads(row))
    r1=np.asarray(row)
    # print(r1[0])

    # print('\n')

# print(routeArray)
# result=cordinate_to_name(24.8961, 67.0814)
# for x in result['results']:
#     if(x['location_type']=='exact'):
#         print(x['sublocality'])uuuuuuuyujkk 


# GET TWO CO-ORDINATE DISTANCE AND TIME
result=get_distance_time()
# print(result['rows'][0]['elements'][0]['duration']['value'])
# print(type(result['rows'][0]['elements'][0]['distance']['value']))
# print(result.decode("utf-8"))


# LOCATE USER TO CAR
nearest_car=locate_user(24.884121,67.177979,24.933786,67.023636)


# GET PRICE FOR RIDE

# fare=sys_based_fare_price(result)
# print(fare)
fare=0
print("1.System Based Calculation \n 2.User Based Calculation \n 3.User Based Calculation only time\n")
user_choice=int(input("Kindly Select AnyOne Option "))
match user_choice:
    case 1:
       fare=sys_based_fare_price(result)
    case 2:
        fare=user_based_fare_price(result)
    case 3:
        fare=user_based_fare_price_on_distance(result)
    case _:
        print("Kindly Select right option")   


if fare==0:
    print("Sorry You Select a wrong choice")
else:
    print(fare)