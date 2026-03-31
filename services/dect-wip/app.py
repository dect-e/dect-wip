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

from database import db # database object
from database import UserExtension,TempExtension,User # database models
scheduler = APScheduler()
login_manager = LoginManager()

instance_path = os.getenv('INSTANCE_PATH')
if(instance_path):
    app = Flask(__name__, instance_path="/tmp/")
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
    query_result = db.session.execute(db.select(User).filter_by(id=user_id)).all()
    # da könnte man mal scalar_one_or_none() ausprobieren, dann fällt der len == 1 quatsch raus

    if len(query_result) == 1:
        return query_result[0][0]

    return None


def getUserExtensions(filterByUserId: User.id | None, searchFor: str | None, showPublicOnly: bool = True) -> list:

    query = db.select(UserExtension).order_by(UserExtension.name.asc())
    
    if showPublicOnly:
        query = query.filter_by(public=True)                     

    if filterByUserId is not None:
        query = query.filter_by(user_id=filterByUserId)

    if searchFor is not None:
        query = query.filter(UserExtension.name.icontains(searchFor))

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
        # REGISTER
        if request.form.get('action') == 'register':

            username = str(request.form.get('username'))
            password1 = str(request.form.get('password1'))
            password2 = str(request.form.get('password2'))

            if username == '' or username is None:
                error_message = 'empty Username is not allowed'
            elif password1 == '' or password1 is None:
                error_message = 'empty Password is not allowed'
            elif password1 != password2:
                error_message = 'Passwords don\'t match'
            else:
                # continue with register
                displayname = username
                username = username.lower()

                # check if username is not already in database
                query_result = db.session.execute(db.select(User).filter_by(username=username)).all()

                if len(query_result) > 0:
                    error_message = 'User already exists'
                else:
                    hasher = argon2.PasswordHasher()

                    user = User()
                    user.username = username
                    user.displayname = displayname
                    user.password = hasher.hash(password=password1)
                    user.is_admin = False

                    db.session.add(user)
                    db.session.commit()

                    info_message = 'account created'


        # LOGIN
        elif request.form.get('action') == 'login':

            username = str(request.form.get('username')).lower()
            password = str(request.form.get('password'))

            if username == '' or username is None:
                error_message = 'empty Username is not allowed'
            elif password == '' or password is None:
                error_message = 'empty Password is not allowed'
            else:

                query_result = db.session.execute(db.select(User).filter_by(username=username)).all()

                if len(query_result) == 1:
                    user = query_result[0][0]  # first [0] is to select first result, [0] is to access the class user
                    try:
                        hasher = argon2.PasswordHasher()
                        pprint.pprint(hasher.verify(hash=user.password, password=password))

                        login_user(user, remember=True,duration=timedelta(days=1))
                        return redirect("/myextensions/", code=302)
                    except argon2.exceptions.VerifyMismatchError:
                        print(username + ' argon2 verification for password failed')
                        error_message = 'wrong login'
                else:
                    print("login: " + username + ' ' + str(len(query_result)) + ' in Database. Don\'t allow login')
                    error_message = 'wrong login'

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


@app.route('/myextensions/', methods=['POST', 'DELETE', 'GET'])
@login_required
def myextensions():

    if request.method == 'POST':
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
            except:
                response = make_response(jsonify( {"message": "extension can't be added. Do you need a voucher?"}), 400)


        else:
            response = make_response(jsonify( {"message": "you need 4 digits"}), 400)
        return response

    if request.method == 'DELETE':

        req_json = request.get_json()
        selection = db.select(UserExtension).filter_by(extension = req_json['extension'])
        ext = db.session.execute(selection).first()

        ext = ext[0]

        if ext.user_id == current_user.id:
            db.session.delete(ext)
            db.session.commit()

            response = make_response(jsonify( {"message": "extension deleted"}), 200)
        else:
            response = make_response(jsonify( {"message": "extension not owned by user"}), 403)
        return response

    if request.method == 'GET':
        exts = getUserExtensions(filterByUserId=current_user.id,searchFor=None,showPublicOnly=False)

        return render_template('myextensions.html.j2', default_data=fetch_default_data_for_templates(), exts=exts)


## API V1

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


    search_string = request.args.get('search')
    
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

    #TODO: add number of extensions added
    
    return "success", 200


def writePjsip():

    query_result = db.session.execute(db.select(UserExtension)).all()
    userExts = [ x[0] for x in query_result ] 
    utilities.pjsipConfig(pjsip_wizard_user_conf, userExts, "user")

    query_result = db.session.execute(db.select(TempExtension)).all()
    tempExts = [ x[0] for x in query_result ] 
    utilities.pjsipConfig(pjsip_wizard_temp_conf, tempExts, "temp_dect")



def trigger():
    with app.app_context():
        #os.system('asterisk -rx "pjsip reload"')
        writePjsip()
        
        from asterisk.ami import AMIClient, SimpleAction

        client = AMIClient(address=dectwip_config['asterisk']['ami']['host'],port=dectwip_config['asterisk']['ami']['port'])
        client.login(username=dectwip_config['asterisk']['ami']['user'],secret=dectwip_config['asterisk']['ami']['password'])

        action = SimpleAction(
            'Command',
            Command = 'pjsip reload'
        )
        client.send_action(action)
        # TODO: verifiy that command was successful
        client.logoff()

def triggerOmm():
    response = requests.get(f"{ommsync_url}/trigger")
    return #TODO: remove



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

    global pjsip_wizard_user_conf, pjsip_wizard_temp_conf, event_name, token_prefix, token_random_count, show_voucher, dectwip_config, ommsync_url

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

    ommsync_url = os.getenv('OMMSYNC_URL', 'http://127.0.0.1:8081')

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
    scheduler.add_job(id='trigger', func=trigger, trigger='interval', seconds=5)
    scheduler.add_job(id='triggerOmm', func=triggerOmm, trigger='interval', seconds=5)
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
