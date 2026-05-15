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
import traceback
import sys
from tools.confighelper import DectWIPConfig

lock = Lock()
app = Flask(__name__)
scheduler = APScheduler()

@app.route('/connect/', methods=['POST'])
def connect():
    with lock:
        req_json = request.get_json()

        user_extension = requests.get(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/GetUserExtensionByToken/{req_json['token']}").json()

        extension = user_extension['extension']
        password = user_extension['password']
        displayname = user_extension['name']

        # TODO get temp_extension from omm
        temp_extenison = requests.get(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/GetTempExtensionByCallerid/{req_json['callerid']}").json()

        # deletes existing users with the same extension
        # this also detaches the (dynamically linked) device
        for user in client.find_users(lambda user: user.num == extension):
            print(f"deleting uid {user.uid} (duplicate of extension {extension})")
            client.delete_user(user.uid)

        new_user = client.create_user(extension)
        client.set_user_sipauth(new_user.uid, extension, password)
        client.set_user_name(new_user.uid, displayname)

        print(f"detaching ppn {temp_extenison['ppn']} from uid {temp_extenison['uid']}")
        client.detach_user_device(temp_extenison['uid'], temp_extenison['ppn'])

        print(f"deleting uid {temp_extenison['uid']}")
        client.delete_user(temp_extenison['uid'])

        print(f"attaching ppn {temp_extenison['ppn']} to uid {new_user.uid}, extension {extension}")
        client.attach_user_device(int(new_user.uid), temp_extenison['ppn'])

        response = make_response(jsonify( {"message": "extension added"}), 200)
    return response

@scheduler.task('interval', id='makeTemps', seconds=5, next_run_time=datetime.now(), max_instances=1)
def makeTemps():
    with lock:
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

            print("new temp extension created", data)

            response = requests.post(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/AddTempExtensionToDB", json=data)
            if response.status_code != 200:
                raise RuntimeError(f"adding temp extension to db failed: {response.status_code} {response.text}")

@scheduler.task('interval', id='enable_subscription', seconds=15, next_run_time=datetime.now(), max_instances=1)
def enable_subscription():
    with lock:
        if config.ommsync_enable_subscription:
            if client.get_dect_auth_code() != config.ommsync_auth_code:
                print(f"setting auth code to {config.ommsync_auth_code}")
                client.set_dect_auth_code(config.ommsync_auth_code)
            if not client.get_device_auto_create():
                print("enabling device auto creation on OMM")
                client.set_device_auto_create(True)
            if client.get_dect_subscription_mode() != 'Configured':
                print("enabling subscription on OMM")
                client.set_dect_subscription_mode('Configured')

def init_ommclient():
    global client

    try:
        client = mitel_ommclient2.OMMClient2(
            host=config.omm_ip,
            port=config.omm_port,
            use_ssl=config.omm_use_ssl,
            username=config.omm_username,
            password=config.omm_password,
            ommsync=True
        )
    except TimeoutError as e:
        raise RuntimeError("Connection to OMM timed out") from e

@scheduler.task('interval', id='retry_connection', seconds=10, next_run_time=datetime.now(), max_instances=1)
def enable_subscription():
    with lock:
        try:
            if not client.ping():
                raise RuntimeError("No reponse received after ping")
        except Exception as e:
            print("ommclient2 ping failed, recreating connection")
            traceback.print_exception(e)

            try:
                init_ommclient()
            except Exception as e:
                print("ommclient2 init connection failed, exiting")
                traceback.print_exception(e)
                sys.exit(1)

def init(config_path):

    # setup global config

    global config

    config = DectWIPConfig(config_path=config_path)

    init_ommclient()

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
