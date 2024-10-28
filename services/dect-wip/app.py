import configparser
import pprint
from datetime import timedelta

import flask
from flask import Flask, render_template, request, jsonify, make_response, Response, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import utilities
import argon2
import os
import namegenerator
import html
import requests


## Read Configuration

config = configparser.ConfigParser()
config.read('/etc/dect-wip.ini')

pjsip_wizard_user_conf = config['asterisk'].get('pjsip_wizard_user_conf')
pjsip_wizard_temp_conf = config['asterisk'].get('pjsip_wizard_temp_conf')

event_name = config['event'].get('name', 'unnamed Event')
token_prefix = config['event'].get('token_prefix', '01990')
token_random_count =  int(config['event'].get('token_random_count', '8'))

database_name = 'database.sqlite3'

app = Flask(__name__)
from database import db # database object
from database import UserExtension,TempExtension,User # database models
scheduler = APScheduler()
login_manager = LoginManager()


## LoginTools

@login_manager.user_loader
def load_user(user_id):
    query_result = db.session.execute(db.select(User).filter_by(id=user_id)).all()
    if len(query_result) == 1:
        return query_result[0][0]

    return None

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


@app.route('/logout/', methods=['GET'])
def logout():
    logout_user()
    return redirect("/login/", code=302)


@app.route('/phonebook/')
def phonebook():
    query_result = db.session.execute(db.select(UserExtension).order_by(UserExtension.extension.asc())).all()

    exts = [x[0] for x in query_result]

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
        ext.token = f'{token_prefix}{utilities.getRandomNumber(token_random_count)}'
        ext.user_id = current_user.id

        if len(ext.extension) == 4 and ext.extension.isdigit():
            db.session.add(ext)
            db.session.commit()

            response = make_response(jsonify( {"message": "extension added"}), 200)

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
        query_result = db.session.execute(db.select(UserExtension).filter_by(user_id=current_user.id)).all()

        exts = [ x[0] for x in query_result ] 

        return render_template('myextensions.html.j2', default_data=fetch_default_data_for_templates(), exts=exts)


## API V1

@app.route('/api/v1/GetUserExtensionByToken/<token>', methods=['GET'])
def GetUserExtensionByToken(token):
    selection = db.select(UserExtension).filter_by(token = token)
    ext = db.session.execute(selection).first()
    return jsonify(ext[0])

@app.route('/api/v1/GetTempExtensionByCallerid/<callerid>', methods=['GET'])
def GetTempExtensionByCallerid(callerid):
    selection = db.select(TempExtension).filter_by(extension = callerid)
    temp_ext = db.session.execute(selection).first()
    return jsonify(temp_ext[0])

@app.route('/api/v1/AddTempExtensionToDB', methods=['POST'])
def AddTempExtensionToDB():

    req_json = request.get_json()
    
    print(req_json)

    ext = TempExtension()
    
    ext.extension = req_json['extension']
    ext.password = req_json['password']
    ext.uid = int(req_json['uid'])
    ext.ppn = int(req_json['ppn'])
    
    db.session.add(ext)
    db.session.commit()
    
    return "sucess", 200

@app.route('/api/v1/phonebook', methods=['GET'])
def phonebook_json():
    query_result = db.session.execute(db.select(UserExtension).order_by(UserExtension.extension.asc())).all()

    names_and_extensions = []

    print(query_result)
    for entry in query_result:
        names_and_extensions.append({"extension": entry[0].extension, "name": entry[0].name})

    return jsonify(names_and_extensions)


def writePjsip():

    query_result = db.session.execute(db.select(UserExtension)).all()
    userExts = [ x[0] for x in query_result ] 
    utilities.pjsipConfig(pjsip_wizard_user_conf, userExts, "user")

    query_result = db.session.execute(db.select(TempExtension)).all()
    tempExts = [ x[0] for x in query_result ] 
    utilities.pjsipConfig(pjsip_wizard_temp_conf, tempExts, "temp_dect")



def trigger():
    with app.app_context():
        writePjsip()
        os.system('asterisk -rx "pjsip reload"')

def triggerOmm():
    response = requests.get("http://127.0.0.1:8081/trigger")



def fetch_default_data_for_templates():
    data = {
        'current_user': current_user,
        'event_name': event_name
        }
    print(data)

    #if current_user.is_authenticated:
    #    data['displayname'] = current_user.displayname

    return data


if __name__ == "__main__":
    # database stuff
    #import caribou
    #caribou.upgrade('instance/' + database_name, 'migrations/')

    # init flask
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_name
    app.secret_key = config['flask'].get('secret_key')
    login_manager.init_app(app)
    db.init_app(app)
    scheduler.init_app(app)

    scheduler.add_job(id='trigger', func=trigger, trigger='interval', seconds=5)
    scheduler.add_job(id='triggerOmm', func=triggerOmm, trigger='interval', seconds=5)
    scheduler.start()

    with app.app_context():
        db.create_all()

    app.add_template_filter(utilities.format_token, 'format_token')

    # run webserver/app
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=True)

