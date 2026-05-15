import os

import mitel_ommclient2
from flask import Flask, request, jsonify, make_response
from flask_apscheduler import APScheduler
import requests
import namegenerator
import utilities
from threading import Lock
import click
from datetime import datetime
from tools.confighelper import DectWIPConfig

print('Make sure Subscription and Auto-Create are enabled')

lock = Lock()
app = Flask(__name__)
scheduler = APScheduler()

@app.route('/connect/', methods=['POST'])
def connect():

    print('obtaining lock')
    with lock:
        print('lock obtained')

        req_json = request.get_json()

        user_extension = requests.get(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/GetUserExtensionByToken/{req_json['token']}").json()

        extension = user_extension['extension']
        password = user_extension['password']
        displayname = user_extension['name']
    
        temp_extenison = requests.get(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/GetTempExtensionByCallerid/{req_json['callerid']}").json()
    
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

@scheduler.task('interval', id='makeTemps', seconds=5, next_run_time=datetime.now(), max_instances=1)
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
    
            response = requests.post(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/AddTempExtensionToDB", json=data)
            print(response.text)

def init(config_path):

    # setup global config

    global config, client

    config = DectWIPConfig(config_path=config_path)

    try:
        client = mitel_ommclient2.OMMClient2(
            host=config.omm_ip,
            port=config.omm_port,
            username=config.omm_username,
            password=config.omm_password,
            ommsync=True
        )
    except (TimeoutError) as e:
        raise RuntimeError("Connection to OMM timed out") from e

    scheduler.init_app(app)
    scheduler.start()


@click.command()
@click.option('--config', 'config_path', envvar='CONFIG_PATH', default='/etc/dect-wip.ini', help='optional config location')
def init_dev(config_path):
    init(config_path)
    # run webserver/app
    app.run(host=config.ommsync_listen_ip, port=config.ommsync_port, debug=False, use_reloader=True)

def init_wsgi():
    init(os.environ.get('CONFIG_PATH', '/etc/dect-wip.ini'))
    return app

if __name__ == "__main__":
    init_dev()
