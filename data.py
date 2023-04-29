# using flask_restful
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import json

from path_2 import locate_user,insert_driver_details,verify_credentials

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
		# data=request.get_json()
		# insert_driver_details(data['Driver_Name'],data['Car_name'],data['Car_num'],data['color'],data['Driver_phone_num'],int(data['num_of_seats']))
		return jsonify({'data':'Success'})

class Driver(Resource):
	def post(self):
		data=request.get_json()
		insert_driver_details(data['Driver_Name'],data['Car_name'],data['Car_num'],data['color'],data['Driver_phone_num'],int(data['num_of_seats']))
		return jsonify({'data':'Success_Data_Inserted'})

class verify_login(Resource):
	def post(self):
		data=request.get_json()
		result=verify_credentials(str(data['phone_num']))
		return jsonify({'data':result})

# adding the defined resources along with their corresponding urls
api.add_resource(find_ride, '/find_ride')
api.add_resource(Driver, '/Driver')
api.add_resource(verify_login, '/verify_user')


# driver function
if __name__ == '__main__':

	app.run(debug = True)
