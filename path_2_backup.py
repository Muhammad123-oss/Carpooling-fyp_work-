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
import datetime


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

# Select fare type
def select_fare_type():
    print("1.System Based Calculation \n 2.User Based Calculation on distance and time \n 3.User Based Calculation only distance\n")
    user_choice=int(input("Kindly Select AnyOne Option "))    
    match user_choice:
        case 1:
            fare_type="system"
            return fare_type
        case 2:
            fare_type="distance_time"
            return fare_type
        case 3:
            fare_type="distance"
            return fare_type
        case _:
            print("Kindly Select right option")
            select_fare_type()

# Add Routes to DB
def route_to_db(response,slat,slong,dlat,dlong):
    route_name=input("Enter route Name: ")
    fare_type=select_fare_type()
    print(fare_type)
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

    cursor.execute("INSERT INTO routes(name,slat,slong,dlat,dlong,fare_type,croute) VALUES(%s,%s,%s,%s,%s,%s,%s)",(route_name,slat,slong,dlat,dlong,fare_type,routeee))
    connection.commit()

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

# Adding user marker to map using lat,long
def add_user_marker_to_map(u_lat,u_long,u_id,m):
    folium.Marker([u_lat,u_long],
    popup="user "+ str(u_id),
    icon=folium.Icon(color="blue",icon="user", prefix='fa')
    ).add_to(m)

# Add User to DB
def add_user(u_src_lat,u_src_long,u_dest_lat,u_dest_long):
    conn=dbconnect()
    cursor=conn.cursor()
    # cursor.execute("INSERT INTO `user` (`u_id`, `u_source_lat`, `u_source_long`, `u_dest_lat`, `u_dest_long`, `time`) VALUES ",('2', '24.881155338755885', '67.17119325702504', '24.887094030441283', '67.14344199686458',ts ))
    cursor.execute("INSERT INTO user(u_source_lat,u_source_long,u_dest_lat,u_dest_long) VALUES(%s,%s,%s,%s)",(u_src_lat,u_src_long,u_dest_lat,u_dest_long))
    conn.commit()

def read_data_from_db(table):
    conn=dbconnect()
    cursor=conn.cursor()
    cursor.execute("select * from {table}".format(table=table))
    record=cursor.fetchall()
    return record

def get_same_route(des_lat,des_long):
    conn=dbconnect()
    # {des_lat:.6f}
    cursor=conn.cursor()
    # print(start_location)
    destination_location=str(des_lat)+", "+str(des_long)
    # SELECT * FROM `routes` where (((24.9085*10000) - CONVERT((slat*10000),INT)) <> 0);
    # cursor.execute("SELECT * FROM `routes` where ((({des_lat:.6f}*1000000) - CONVERT((dlat*1000000),INT)) = 0)  AND \
    #     ((({des_long:.6f}*1000000) - CONVERT((dlong*1000000),INT)) = 0)"\
    #     .format(des_long=des_long,des_lat=des_lat))
    cursor.execute("SELECT * FROM `routes` where croute LIKE '%{s}%'".format(s=destination_location))
    return cursor.fetchall()

def calculate_fare_for_user(result,user_choice):
    # print(user_choice)
    match user_choice:
        case 'system':
            fare=sys_based_fare_price(result)
            fare=format(fare, '.2f')
            return fare
        case 'distance_time':
            fare=user_based_fare_price(result)
            fare=format(fare, '.2f')
            return fare
        case 'distance':
            fare=user_based_fare_price_on_distance(result)
            fare=format(fare, '.2f')
            return fare
        case _:
            print("Invalid")

def locate_user(user_src_lat,user_src_long,user_dest_lat,user_dest_long):
    # Checking for similar destination routes (dest long lat ,source long lat)
    dest_data=get_same_route(user_dest_lat,user_dest_long)
    cmp_route_arr=[]
    fare_type_selection=[]
    if(dest_data):
        for row in dest_data:
            # print(json.loads(row))
            r1=np.asarray(row)
            #Converting json(string) column from DB to Python list
            cmp_route=json.loads(r1[7])         
            # print(r1[1])
            fare_type_selection.append(r1[6])
            # print(r1[6])
            # print(len(cmp_route))
            # print(cmp_route) 
            cmp_route_arr.append(cmp_route) 
            # print(cmp_route)
            # print(np.ndim(cmp_route)) #return the number of dimensions of an array
            # print('\n')
        # print(cmp_route[0])
        # dist_in_km=find_dist_btw_point(user_src_lat,user_src_long,user_dest_lat,user_dest_long) #Distance function Test 
        # print(dist_in_km)

        num_rows=len(cmp_route_arr)
        # print("ARRAY VAL")
        nearest_dest={}
        # print(cmp_route_arr)
        # Calculating User Distance from Vehicle Route lat,lon
        count=1
        for route in range(num_rows):
            route_len=len(cmp_route_arr[route])
            driver_choice=fare_type_selection[route]
            nearest_path_available=False
            min =999
            pickup_point_lat=0.0
            pickup_point_long=0.0
            for row in range(route_len):
                dist_in_km=find_dist_btw_point(user_src_lat,user_src_long,cmp_route_arr[route][row][0],cmp_route_arr[route][row][1])
                if(dist_in_km<8.5):
                    if(dist_in_km<min):
                        # getting minimum dist in 'min' variable and storing it's lat/long
                        nearest_path_available=True
                        min=dist_in_km
                        pickup_point_lat= cmp_route_arr[route][row][0]
                        pickup_point_long= cmp_route_arr[route][row][1]


                    #  For Knowledge: float(format(dist_in_km, '.2f')) If we want to get float value upto 2 decimal points
                else:
                    # print(dist_in_km)
                    continue
            # Nested 'for loop' body ends here
            if(nearest_path_available):
                name=' Route '+str(count) #Setting a name for nested dictionary  
                nearest_dest[name]={} #Initializing a dictionary that to be nested in a 'nearest_dest{}'
                nearest_dest[name]['min']=format(min, '.2f')
                nearest_dest[name]['lat']=pickup_point_lat
                nearest_dest[name]['long']=pickup_point_long
                result=get_distance_time(pickup_point_lat,pickup_point_long,user_dest_lat,user_dest_long)
                nearest_dest[name]['ride_fare']=calculate_fare_for_user(result,driver_choice)
                count=count+1
        #'for loop' body ends here
        # print("Nearest KEY Riders Array")
        # print(nearest_dest)
        return nearest_dest
    else:
        print("No ride Available")
        sorry="sorry"
        return sorry

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

"""
Setting Markers to nearest available vehicles
"""
def put_markers_to_nearest_vehicles(available_rides,m):
    # print(available_rides)
    # print(type(available_rides['route0']['lat']))
    pickup_point_names = []
    for points in available_rides:
        response=cordinate_to_name(available_rides[points]['lat'],available_rides[points]['long'])
        # print(response)
        for location_name in response['results']:
            if(location_name['location_type']=='centroid'):
                pickup_point_names.append(location_name['address'])
                # print(location_name['address'])
                folium.Marker([available_rides[points]['lat'],available_rides[points]['long']],
                popup=location_name['address'],
                icon=folium.Icon(color="green",icon="car", prefix='fa')
                ).add_to(m)
                break
        # end of inner loop
    # end of outer loop
    return pickup_point_names


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


def get_distance_time(src_lat,src_long,dest_lat,dest_long):
    src_points=str(src_lat)+','+str(src_long)
    dest_points=str(dest_lat)+','+str(dest_long)
    query={"origins":src_points,"destinations":dest_points,"departure_time":"now","key":"efdyNURa3j71WqUimAmpJzAtnG359"}
    response=requests.get("https://api.distancematrix.ai/maps/api/distancematrix/json",params=query)
    return response.json()
    # conn = http.client.HTTPSConnection("api.distancematrix.ai")
    # conn.request("GET", "/maps/api/distancematrix/json?origins=24.878937747538565%2C67.1884669257004&destinations=24.857142456865084%2C67.26475889871588&departure_time=now&key=ntTWUnz82Npcyzj2xFj0yT8vojEjJ")
    # res = conn.getresponse()
    # data = res.read()
    # return data

def display_ride_details(available_rides,pickup_point_names):
    count=0
    print("Available Routes \n")
    for i in available_rides:
        print(i)
        print(" Minimum Distance :",available_rides[i]['min'])
        print(" Ride Fare        :",available_rides[i]['ride_fare'])
        print(" Pick Up Point    :",pickup_point_names[count])
        print('\n')
        count=count+1

    # print(available_rides)
    # print(pickup_point_names)


# Main

# setting up database
connection=dbconnect()
cursor=connection.cursor()

slat=24.77954760427206
slong=67.09080664088563
dlat=24.855828584328297
dlong=67.0284733543784

# moin khan to zainab market: 24.77954760427206, 67.09080664088563,24.855828584328297, 67.0284733543784
# response = get_directions_response(48.34364,10.87474,48.37073,10.909257)
# fast to halt: 24.908460648396446, 67.220800769881,24.848005654110313, 66.99520521035566
# halt to luckyone: 24.884609570015506, 67.17634308152044,24.93263472395275, 67.08725306802955

response = get_directions_response(slat,slong,dlat,dlong)
# route_to_db(response,slat,slong,dlat,dlong)
m = create_map(response)

# m.save('./route_map.`html')

# Adding User to DB
# add_user(24.881155338755885,67.17119325702504,24.887094030441283,67.14344199686458)
# add_user(24.915400208475877, 67.10005999686508,24.933473, 67.085896)
# add_user(24.922868867283775,67.09273973268596,24.933467, 67.087321)
# add_user(24.916987109609163,67.09639826577977,24.933391, 67.087562)


# Call for adding User Marker
# add_user_marker_to_map(24.881155338755885, 67.17119325702504,1,m)
user_info=read_data_from_db("user")
for row in user_info:
    r1=np.asarray(row)
    add_user_marker_to_map(r1[1],r1[2],r1[0],m)
    # print(r1[0])


available_rides=locate_user(24.881155338755885,67.17119325702504,24.779736, 67.090401)
pickup_point_names=put_markers_to_nearest_vehicles(available_rides,m)
display_ride_details(available_rides,pickup_point_names)
m.save('./route_map.html')
# No new table required if we are going for each row a route. Helpful when multiple route has same path
# cursor.execute("INSERT INTO routes(route_no,complete_route) VALUES(%s,%s)",(routeee))

# route_to_db(response,slat,slong,dlat,dlong)
connection.commit()

# # # Checking for similar destination routes (dest long lat ,source long lat)
# # dest_data=get_same_route(24.848005, 66.995209)
# # for row in dest_data:
# #     # print(json.loads(row))
# #     r1=np.asarray(row)
# #     #Converting json(string) column from DB to Python list
# #     cmp_route=json.loads(r1[6])  
# #     # print(len(cmp_route))

# #     # print('\n')

# # reading file
# cursor.execute("select croute from routes")
# record=cursor.fetchall()

# for row in record:
#     # print(json.loads(row))
#     r1=np.asarray(row)
#     # print(r1[0])

#     # print('\n')

# # print(routeArray)
# # result=cordinate_to_name(24.8961, 67.0814)
# # for x in result['results']:
# #     if(x['location_type']=='exact'):
# #         print(x['sublocality'])uuuuuuuyujkk 


# # GET TWO CO-ORDINATE DISTANCE AND TIME
# result=get_distance_time()
# # print(result['rows'][0]['elements'][0]['duration']['value'])
# # print(type(result['rows'][0]['elements'][0]['distance']['value']))
# # print(result.decode("utf-8"))


# # LOCATE USER TO CAR
# nearest_car=locate_user(24.884121,67.177979,24.933786,67.023636)


# # GET PRICE FOR RIDE

# # fare=sys_based_fare_price(result)
# # print(fare)
# fare=0
# print("1.System Based Calculation \n 2.User Based Calculation \n 3.User Based Calculation only time\n")
# user_choice=int(input("Kindly Select AnyOne Option "))
# match user_choice:
#     case 1:
#        fare=sys_based_fare_price(result)
#     case 2:
#         fare=user_based_fare_price(result)
#     case 3:
#         fare=user_based_fare_price_on_distance(result)
#     case _:
#         print("Kindly Select right option")   


# if fare==0:
#     print("Sorry You Select a wrong choice")
# else:
#     print(fare)