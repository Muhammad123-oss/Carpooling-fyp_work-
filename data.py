# using flask_restful
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import json

from path_2 import locate_user,insert_driver_details,verify_credentials,update_seats,get_directions_response,route_to_db,insert_passenger_details,get_driver_history

# creating the flask app
app = Flask(__name__)
# creating an API object
api = Api(app)

# making a class for a particular resource
# the get, post methods correspond to get and post requests
# they are automatically mapped by flask_restful.
# other methods include put, delete, etc.
class find_ride(Resource):

	# corresponds to the GET request.
	# this function is called whenever there
	# is a GET request for this resource
	def get(self):
		# {\"slat\":\"24.873003196931517\",\"slong\":\"67.09391657264112\",\"dlat\":\"24.924508\",\"dlong\":\"67.030546\"}
		# data=request.json
		data=request.args.to_dict()
		available_rides=locate_user(float(data['slat']),float(data['slong']),float(data['dlat']),float(data['dlong']),int(data['require_seats']))
		# print(float(data['slat']))
		return jsonify({'data': available_rides})

	# Corresponds to POST request
	def post(self):
		data=request.get_json()
		response=update_seats(int(data['num_of_seats_booked']),int(data['route_id']))
		return jsonify({'data':response})

class Driver(Resource):
	def post(self):
		data=request.get_json()
		insert_driver_details(data['Driver_Name'],data['Car_name'],data['Car_num'],data['color'],data['Driver_phone_num'],int(data['num_of_seats']))
		return jsonify({'data':'Success_Data_Inserted'})
	
	def get(self):
		data=request.args.to_dict()
		response=get_driver_history(data['driver_id'])
		return jsonify({'data':response})

class Passenger(Resource):
	def post(self):
		data=request.get_json()
		insert_passenger_details(data['passenger_name'],data['cnic'],data['phone_num'])
		return jsonify({'data':'Success_Data_Inserted'})

class verify_login(Resource):
	def post(self):
		data=request.get_json()
		result=verify_credentials(str(data['phone_num']),str(data['user_type']))
		return jsonify({'data':result})

class offer_pool(Resource):
	def post(self):
		data=request.get_json()
		complete_route=get_directions_response(float(data['slat']),float(data['slong']),float(data['dlat']),float(data['dlong']))
		response=route_to_db(complete_route,str(data['route_name']),float(data['slat']),float(data['slong']),float(data['dlat']),float(data['dlong']),int(data['driver_id']),int(data['available_seats']),str(data['fare_type']),float(data['fare_per_km']),float(data['fare_per_min']))
		return jsonify({'data':'Route Inserted'})

# adding the defined resources along with their corresponding urls
api.add_resource(find_ride, '/find_ride')
api.add_resource(Driver, '/driver')
api.add_resource(Passenger, '/insert_passenger')
api.add_resource(verify_login, '/verify_user')
api.add_resource(offer_pool, '/add_route')


# driver function
if __name__ == '__main__':

	app.run(debug = True)
