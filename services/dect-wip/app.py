import configparser
import pprint
import utilities
import argon2
import os
import html
from datetime import timedelta
from flask import Flask, render_template, request, jsonify, make_response, Response, redirect, abort
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import click
import requests
from flasgger import Swagger
from threading import Lock
from datetime import datetime

from database import db # database object
from database import UserExtension,TempExtension,User # database models
scheduler = APScheduler()
login_manager = LoginManager()

instance_path = os.getenv('INSTANCE_PATH')
if(instance_path):
    app = Flask(__name__, instance_path=instance_path)
else:
    app = Flask(__name__)

# config

application_config = {}

## LoginTools

@login_manager.user_loader
def load_user(user_id):
    """
    provide information about the user in flask
    """
    user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one_or_none()
    return user



def getUserExtensions(filterByUserId: User.id | None, searchFor: str | None, showPublicOnly: bool = True) -> list:
    """
    Retrieve user extensions from the database sorted by name

    Args:
        filterByUserId: Restrict results to extensions owned by the given user ID
        searchFor: SQL LIKE pattern used to filter extension names
        showPublicOnly: only public extensions are returned

    Returns:
        list: list of user extensions sorted by name
    """
    query = db.select(UserExtension).order_by(UserExtension.name.asc())

    if showPublicOnly:
        query = query.filter_by(public=True)                     

    if filterByUserId is not None:
        query = query.filter_by(user_id=filterByUserId)

    if searchFor is not None:
        query = query.filter(UserExtension.name.like(searchFor))

    return db.session.execute(query).scalars().all()



## Routes

@app.route('/')
def default(): 
    return redirect("/phonebook/", code=302)
    #return render_template('base.html.j2', default_data=fetch_default_data_for_templates())


@app.route('/login/', methods=['GET', 'POST'])
def login():
    error_message = ''
    info_message = ''

    # POST - Register or Login?
    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')
        password_repeat = request.form.get('password_repeat')
        action = request.form.get('action')


        # REGISTER
        if action == 'register':

            if username == '' or username is None:
                error_message = 'empty Username is not allowed'
            elif password == '' or password is None:
                error_message = 'empty Password is not allowed'
            elif password != password_repeat:
                error_message = 'Passwords don\'t match'
            else:
                # continue with register
                displayname = str(username)
                username = str(username).lower()
                password = str(password)

                # check if username is not already in database
                existing_user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

                if existing_user is not None:
                    error_message = 'User already exists'
                else:
                    hasher = argon2.PasswordHasher()

                    user = User()
                    user.username = username
                    user.displayname = displayname
                    user.password = hasher.hash(password)
                    user.is_admin = False

                    db.session.add(user)
                    db.session.commit()

                    info_message = 'account created'

                    login_user(user, remember=True,  duration=timedelta(days=1))
                    return redirect("/myextensions/", code=302)

        # LOGIN
        elif action == 'login':

            if username == '' or username is None:
                error_message = 'empty Username is not allowed'
            elif password == '' or password is None:
                error_message = 'empty Password is not allowed'
            else:

                username = str(username).lower()
                password = str(password)

                user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

                if user is not None:

                    try:
                        hasher = argon2.PasswordHasher()
                        if hasher.verify(hash=user.password, password=password):
                            login_user(user, remember=True, duration=timedelta(days=1))
                            return redirect("/myextensions/", code=302)
                        
                    except argon2.exceptions.VerifyMismatchError:
                        pass

                error_message = 'login error, check username and password'


    # Fallback - used if login not successful or no login attempt
    return render_template('login.html.j2', default_data=fetch_default_data_for_templates(), error_message=error_message, info_message=info_message)

 
@app.route('/admin/', methods=['GET'])
@login_required
def admin():
    cu = db.session.execute(db.select(User).where(User.id==current_user.id)).scalar_one()
    
    if cu.is_admin: 
        return "<p>Hello, Admin!</p>"
    else:
        return abort(403)


@app.route('/logout/', methods=['GET'])
def logout():
    logout_user()
    return redirect("/login/", code=302)


@app.route('/phonebook/')
def phonebook():

    exts = getUserExtensions(filterByUserId=None,searchFor=None,showPublicOnly=True)

    return render_template('phonebook.html.j2', default_data=fetch_default_data_for_templates(), exts=exts)


@app.route('/myextensions/', methods=['GET'])
@login_required
def myextensions():
    exts = getUserExtensions(filterByUserId=current_user.id, searchFor=None, showPublicOnly=False)

    return render_template('myextensions.html.j2', default_data=fetch_default_data_for_templates(), exts=exts)


## API V1

@app.route('/api/v1/CreateUserExtension', methods=['POST'])
@login_required
def CreateUserExtension():
    """
    Create a user extension
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - extension
            - name
            - info
            - public
          properties:
            extension:
              type: string
            name:
              type: string
            info:
              type: string
            public:
              type: boolean
    responses:
      200:
        description: User extension successfully added
    """
    req_json = request.get_json()
    ext = UserExtension()

    ext.extension = html.escape(req_json['extension'])
    ext.password = utilities.getRandomNumber(20)
    ext.name = html.escape(req_json['name'])
    ext.info = html.escape(req_json['info'])
    ext.public = bool(req_json['public'])
    ext.token = f'{token_prefix}{utilities.getRandomNumber(token_random_count)}'
    ext.user_id = current_user.id

    if len(ext.extension) == 4 and ext.extension.isdigit() and int(ext.extension[:1]) > 0:
        try:
            db.session.add(ext)
            db.session.commit()

            response = make_response(jsonify( {"message": "extension added"}), 200)

            schedule_asterisk_configuration_update()
        except:
            response = make_response(jsonify( {"message": "extension can't be added. Do you need a voucher?"}), 400)

    else:
        response = make_response(jsonify( {"message": "you need 4 digits"}), 400)
    return response

@app.route('/api/v1/DeleteUserExtension', methods=['POST'])
@login_required
def DeleteUserExtension():
    """
    Delete a user extension
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - extension
          properties:
            extension:
              type: string
    responses:
      200:
        description: User extension successfully deleted
    """
    req_json = request.get_json()
    selection = db.select(UserExtension).filter_by(extension = req_json['extension'])
    ext = db.session.execute(selection).first()

    ext = ext[0]

    if ext.user_id == current_user.id:
        db.session.delete(ext)
        db.session.commit()

        response = make_response(jsonify( {"message": "extension deleted"}), 200)

        schedule_asterisk_configuration_update()
    else:
        response = make_response(jsonify( {"message": "extension not owned by user"}), 403)
    return response

@app.route('/api/v1/GetUserExtensions', methods=['GET'])
@login_required
def GetUserExtensions():
    """
    Get all extensions of the current user
    ---
    responses:
      200:
        schema:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
                description: user name
              extension:
                type: string
              token:
                type: string
              password:
                type: string
              info:
                type: string
    """
    exts = [
        {
            "name": ext.name,
            "extension": ext.extension,
            "token": ext.token,
            "password": ext.password,
            "info": ext.info,
        }
        for ext in getUserExtensions(filterByUserId=current_user.id, searchFor=None, showPublicOnly=False)
    ]
    response = make_response(jsonify(exts), 200)
    return response

# TODO: change <token> to POST Parameter
# TODO: fix 500 server error if no extensions is found
@app.route('/api/v1/GetUserExtensionByToken/<token>', methods=['GET'])
def GetUserExtensionByToken(token):
    """
    Get user extension by token
    ---
    parameters:
      - name: token
        in: path
        type: string
        required: true
    responses:
      200:
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
              description: user name
            extension:
              type: string
            token:
              type: string
    """
    selection = db.select(UserExtension).filter_by(token = token)
    ext = db.session.execute(selection).first()
    return jsonify(ext[0])

@app.route('/api/v1/GetTempExtensionByCallerid/<callerid>', methods=['GET'])
def GetTempExtensionByCallerid(callerid):
    """
    Get temporary extension by caller ID
    ---
    parameters:
      - name: callerid
        in: path
        type: string
        required: true
    responses:
      200:
        schema:
          type: object
          properties:
            id:
              type: integer
            extension:
              type: string
            name:
              type: string
    """

    selection = db.select(TempExtension).filter_by(extension = callerid)
    temp_ext = db.session.execute(selection).first()
    return jsonify(temp_ext[0])

@app.route('/api/v1/AddTempExtensionToDB', methods=['POST'])
def AddTempExtensionToDB():
    """
    Add temporary extension to the database
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - extension
            - password
            - uid
            - ppn
          properties:
            extension:
              type: string
            password:
              type: string
            uid:
              type: integer
            ppn:
              type: integer
    responses:
      200:
        description: Extension successfully added
    """


    req_json = request.get_json()
    
    print(req_json)

    ext = TempExtension()
    
    ext.extension = req_json['extension']
    ext.password = req_json['password']
    ext.uid = int(req_json['uid'])
    ext.ppn = int(req_json['ppn'])
    
    db.session.add(ext)
    db.session.commit()

    schedule_asterisk_configuration_update()
    
    return "success", 200

# TODO: fix broaken searchstring
@app.route('/api/v1/phonebook', methods=['GET'])
def phonebook_json():
    """
    Get phonebook entries
    ---
    parameters:
      - name: search
        in: query
        type: string
        required: false
    responses:
      200:
        schema:
          type: array
          items:
            type: object
            properties:
              extension:
                type: string
              name:
                type: string
    """


    search_string = f"%{request.args.get('search')}%"
    
    query_result = getUserExtensions(filterByUserId=None,searchFor=search_string,showPublicOnly=True)

    names_and_extensions = [{"extension": entry.extension, "name": entry.name} for entry in query_result]

    return jsonify(names_and_extensions)

@app.route('/api/v1/ClaimExtensionByVoucher/', methods=['POST'])
@login_required
def ClaimExtensionByVoucher():
    """
    Claim an extension using a voucher code
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - voucher
          properties:
            voucher:
              type: string
    responses:
      200:
        description: Extension successfully claimed
      400:
        description: Missing or empty voucher field
    """


    req_json = request.get_json()
    print(req_json)

    if "voucher" not in req_json:
        return "Field 'voucher' not found", 400

    if not len(req_json['voucher']) > 0:
        return "Field 'voucher' is empty", 400

    voucher = req_json["voucher"].replace(' ', '') #TODO: imporve space handling
    db.session.execute(
        db.update(UserExtension).filter_by(voucher = voucher).values(user_id=current_user.id)
    )
    db.session.commit()

    schedule_asterisk_configuration_update()

    #TODO: add number of extensions added
    
    return "success", 200


lock_asterisk = Lock()

# generates Asterisk config
def writePjsip():
    if lock_asterisk.locked():
        raise RuntimeError("the writePjsip function assumes that the asterisk lock is already acquired by the calling function")

    query_result = db.session.execute(db.select(UserExtension)).all()
    userExts = [ x[0] for x in query_result ] 
    utilities.pjsipConfig(pjsip_wizard_user_conf, userExts, "user")

    query_result = db.session.execute(db.select(TempExtension)).all()
    tempExts = [ x[0] for x in query_result ] 
    utilities.pjsipConfig(pjsip_wizard_temp_conf, tempExts, "temp_dect")

# Generates new Asterisk configs and pokes Asterisk to reload configs
@scheduler.task('interval', id='update_asterisk_configuration', seconds=300, next_run_time=datetime.now(), max_instances=1)  # every 5min, is called immediately on changes in the db
def update_asterisk_configuration():
    with lock_asterisk:
        with app.app_context():
            writePjsip()

            from asterisk.ami import AMIClient, SimpleAction
            client = AMIClient(
                address=dectwip_config['asterisk']['ami']['host'],
                port=dectwip_config['asterisk']['ami']['port']
            )
            client.login(
                username=dectwip_config['asterisk']['ami']['user'],
                secret=dectwip_config['asterisk']['ami']['password']
            )
            try:
                action = SimpleAction('Command', Command='module reload res_pjsip_config_wizard.so')
                result = client.send_action(action)
                response = result.response if hasattr(result, 'response') else result

                status = getattr(response, 'status', '').lower()
                output = response.keys.get('Output', '') if isinstance(getattr(response, 'keys', None), dict) else ''

                if not (status == 'success' and 'reloaded successfully' in output.lower()):
                    print(f"PJSIP reload failed — status: {status}, output: {output}")
                    raise RuntimeError(f"PJSIP reload failed: {output or status}")
            finally:
                client.logoff()

# schedules a task to poke asterisk soon^TM
def schedule_asterisk_configuration_update():
    scheduler.modify_job('update_asterisk_configuration', next_run_time=datetime.now())


def fetch_default_data_for_templates():
    data = {
        'current_user': current_user,
        'event_name': event_name,
        'show_voucher': show_voucher
        }
    print(data)

    #if current_user.is_authenticated:
    #    data['displayname'] = current_user.displayname

    return data

def init(config_path):

    # setup global config

    global pjsip_wizard_user_conf, pjsip_wizard_temp_conf, event_name, token_prefix, token_random_count, show_voucher, dectwip_config

    print(f'Using config: {config_path}')

    config = configparser.ConfigParser()
    config.read(config_path)

    pjsip_wizard_user_conf = config['asterisk'].get('pjsip_wizard_user_conf')
    pjsip_wizard_temp_conf = config['asterisk'].get('pjsip_wizard_temp_conf')
    ami_pw = (
    open(os.getenv('AMI_PW_PATH')).read().strip() if os.getenv('AMI_PW_PATH') else config['asterisk'].get('ami_password')
    )
    dectwip_config = {
        'asterisk': {
            'ami': {
                'host': config['asterisk'].get('ami_host'),
                'port': int(config['asterisk'].get('ami_port')),
                'user': config['asterisk'].get('ami_user'),
                'password': ami_pw
                
            }
        },
        'flask': { 
            'swagger': {
                'enabled': config['flask'].get('swagger_enabled', 'False')
            }
        }
    }

    event_name = config['event'].get('name', 'unnamed Event')
    token_prefix = config['event'].get('token_prefix', '01990')
    token_random_count = int(config['event'].get('token_random_count', '8'))
    show_voucher = config['event'].get('show_voucher', 'True')

    # init flask
    app.secret_key = (
    open(os.getenv('FLASK_SECRET_KEY_PATH')).read().strip() 
    if os.getenv('FLASK_SECRET_KEY_PATH') else config['flask'].get('secret_key')
    )

    # autogenerate secret_key if not provided
    if not app.secret_key:
        app.secret_key = utilities.getRandomStr(16)
        print(f'generated secret_key: {app.secret_key}')
        config.set('flask', 'secret_key', app.secret_key)
        with open(config_path, 'w') as configfile:
            config.write(configfile)

    # database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
    db.init_app(app)
    with app.app_context():
        db.create_all()

    login_manager.init_app(app)

    scheduler.init_app(app)
    scheduler.start()

    app.add_template_filter(utilities.format_token, 'format_token')

    # run swagger
    if dectwip_config['flask']['swagger']['enabled'] == 'True':
        print('enabling Swagger - /apidocs/')
        swagger = Swagger(app)

@click.command()
@click.option('--config', 'config_path', envvar='CONFIG', default='/etc/dect-wip.ini', help='optional config location')
def init_dev(config_path):
    init(config_path)
    # run webserver/app
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=True)

def init_wsgi():
    config_path = os.getenv('CONFIG', '/etc/dect-wip.ini')
    init(config_path)
    return app

if __name__ == "__main__":
    init_dev()
