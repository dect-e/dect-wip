import configparser
import mitel_ommclient2
from flask import Flask, request, jsonify, make_response
import requests
import namegenerator
import utilities
from threading import Lock
import click
import os

print('Make sure Subscription and Auto-Create are enabled')

lock = Lock()
app = Flask(__name__)

@app.route('/connect/', methods=['POST'])
def connect():

    print('obtaining lock')
    with lock:
        print('lock obtained')

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
        # no implemented in current ommclient ...
        #client.delete_user(uid)
    
        response = make_response(jsonify( {"message": "extension added"}), 200)
    return response


@app.route('/trigger/', methods=['GET'])
def makeTemps():
    print("lets go")

    print('obtaining lock')
    with lock:
        print('lock obtained')
    
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

def init(config_path):

    # setup global config

    global config, dect_wip_ip, omm_ip, omm_port, omm_username, omm_password, client 

    print(f'Using config: {config_path}')

    config = configparser.ConfigParser()
    config.read(config_path)

    omm_ip = config['omm'].get('ip')
    omm_port = config['omm'].getint('port')
    omm_username = config['omm'].get('username')
    omm_password = (
    open(os.getenv('OMM_PW_PATH')).read().strip() 
    if os.getenv('OMM_PW_PATH') else config['omm'].get('password')
    )

    try:
        client = mitel_ommclient2.OMMClient2(
            host=omm_ip,
            port=omm_port,
            username=omm_username,
            password=omm_password,
            ommsync=True
        )
    except (TimeoutError) as e:
        raise RuntimeError("Connection to OMM timed out") from e

    dect_wip_ip = os.getenv('DECT_WIP_IP', '127.0.0.1:8080')


@click.command()
@click.option('--config', 'config_path', envvar='CONFIG', default='/etc/dect-wip.ini', help='optional config location')
def init_dev(config_path):
    init(config_path)
    # run webserver/app
    app.run(host='0.0.0.0', port=8081, debug=False, use_reloader=True)

def init_wsgi():
    config_path = os.getenv('CONFIG', '/etc/dect-wip.ini')
    init(config_path)
    return app

if __name__ == "__main__":
    init_dev()
