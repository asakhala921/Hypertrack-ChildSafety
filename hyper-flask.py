
# import http.server
# import socketserver
from pymongo import MongoClient
from urllib.parse import urlparse
from urllib.parse import parse_qs
from hypertrack.rest import Client
from hypertrack.exceptions import HyperTrackException
import json
import flask
import os
from flask import Flask, jsonify
from flask import make_response, request, abort
import hashlib
import hmac
import requests

account_id = "E-9uKtxUW_ull4ejgUtyl_phnjc"
secret_key = "HtJiCeeSivCaRiPROQSWrQjFivcPoxGTtrrcGO_qES2y-t_lL-MTCA"
device_id = "0DA947BB-D69D-420C-AB68-5EE2005779CA"
hypertrack = Client(account_id, secret_key)
hypertrack.devices.start_tracking(device_id)

mongo_client = MongoClient() 
mydatabase = mongo_client['test'] 

app = flask.Flask(__name__)
app.config["DEBUG"] = True
locations_sofar = [] #temporaty buffer of recent location data

@app.route('/', methods=['GET'])
def home(): 
    devices = hypertrack.devices.get_all()
    # print(devices)

    #  custom HTML code
    pretty = json.dumps(devices, indent=4, sort_keys=True)
    html = f"<html><head></head><body><h1>Hello !</h1> <h2>{pretty}</h2></body></html>"
    return html

@app.route('/not-found', methods=['GET'])
def errr():
    abort(404)
    return jsonify({'task': '404'})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/post', methods=['POST'])
def create_task():
    print ("Im IN POST")
    rcvd = request.json
    print (rcvd)

    if not rcvd:
        abort(400)

    locations_sofar.append(rcvd)

    #parse event, if type == geofence , value ..entry or exit 
    for i in range(len(rcvd)):
        if rcvd[i]["type"] == "geofence":

            out = (f"person has {rcvd[i]['data']['value']}ed location ") #{rcvd[i]['geofence_metadata']['name']}
            if 'geofence_metadata' in rcvd[i]:
                out = (f"person has {rcvd[i]['data']['value']}ed location {rcvd[i]['geofence_metadata']['name']} ") 

            # send the update to the parent
            url = "https://www.fast2sms.com/dev/bulkV2"
            querystring = {"authorization":"KzT4d3E2Mkf6Gn57iXjORvh1q9ZyaLmUQptexsH8VgrScbPDw0lSiKGLBmRdwPJaFfVpcjEIvYC8Wbxe",
            "message":out,"language":"english","route":"q","numbers":"9011220099"}
            print("geofence is = ", out)
            headers = {'cache-control': "no-cache" }
            response = requests.request("GET", url, headers=headers, params=querystring)
            print("sms sent")
            print(response.text)
    
    mydatabase.hypertrack.insert_many(rcvd)
    return jsonify({'location': "added"}), 201

@app.route('/see', methods=['GET'])
def see():
    print ("Im IN /see")
    html = f"<html><head></head><body><h1>Location buffer has :</h1> <h2>{str(locations_sofar)}</h2></body></html>"
    print(locations_sofar)

    return html#jsonify(locations_sofar)

@app.route('/geofence', methods=['GET'])
def geofence():
    response = requests.request("GET", "https://v3.api.hypertrack.com/geofences/d49f4074-c12e-454f-aada-0b5878bee44e", auth=(account_id,secret_key))
    a = list(mydatabase.hypertrack.find({}, sort=[( '_id', -1 )]))
    print (a)
    print (response)
    #if latest from webhook outside geofence ...alert
    print ("Im IN GEOFENCE GET")
    
app.run() 
hypertrack.devices.stop_tracking(device_id)



