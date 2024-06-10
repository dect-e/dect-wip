import configparser
import mitel_ommclient2
from flask import Flask, request, jsonify, make_response
import requests
import namegenerator
import utilities


dect_wip_ip = "127.0.0.1:8080"

print('Make sure Subscription and Auto-Create are enabled')

config = configparser.ConfigParser()
config.read('config.ini')

omm_ip = config['omm'].get('ip')
omm_port = config['omm'].getint('port')
omm_username = config['omm'].get('username')
omm_password = config['omm'].get('password')

client = mitel_ommclient2.OMMClient2(host=omm_ip, port=omm_port, username=omm_username, password=omm_password, ommsync=True)

app = Flask(__name__)

@app.route('/connect/', methods=['POST'])
def connect():

    req_json = request.get_json()

    user_extension = requests.get(f"http://{dect_wip_ip}/api/v1/GetUserExtensionByToken/{req_json['token']}").json()

    extension = user_extension['extension']
    password = user_extension['password']
    displayname = user_extension['name']

    temp_extenison = requests.get(f"http://{dect_wip_ip}/api/v1/GetTempExtensionByCallerid/{req_json['callerid']}").json()

    ppn = temp_extenison['ppn']
    uid = temp_extenison['uid']

    print(ppn)
    print(uid)

    client.detach_user_device(uid,ppn)

    newuser = client.create_user(extension)
    client.set_user_sipauth(newuser.uid, extension, password)
    client.set_user_name(newuser.uid, displayname)
    
    print(client.attach_user_device(int(newuser.uid), ppn))
    #client.delete_user(uid)

    response = make_response(jsonify( {"message": "extension added"}), 200)
    return response


@app.route('/trigger/', methods=['GET'])
def makeTemps():
    print("lets go")

    for device in list(client.find_devices(lambda d: d.relType == mitel_ommclient2.types.PPRelTypeType("Unbound"))):
        extension = 't_' + namegenerator.generate_name() + utilities.getRandomNumber(4)
        password = utilities.getRandomStr(20)

        newuser = client.create_user(extension)
        client.set_user_sipauth(newuser.uid, extension, password)
        client.set_user_name(newuser.uid, extension[2:21])
        client.attach_user_device(int(newuser.uid), int(device.ppn))

        data = {
            "extension": extension,
            "password": password,
            "uid": newuser.uid,
            "ppn": device.ppn
        }

        print(data)

        response = requests.post(f"http://{dect_wip_ip}/api/v1/AddTempExtensionToDB", json=data)
        print(response.text)

    return "success", 200


if __name__ == "__main__":
    #app.secret_key = config['flask'].get('secret_key')

    # run webserver/app
    app.run(host='0.0.0.0', port=8081, debug=True, use_reloader=True)
