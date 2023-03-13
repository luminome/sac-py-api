#!/usr/bin/env python3

# from flask import Flask, jsonify, abort, render_template, request
from flask import Flask, abort, request, jsonify, g, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
#from itsdangerous import (BadSignature, SignatureExpired)
#from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer

from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

import jwt

from flaskext.markdown import Markdown
from functools import wraps

from os import getpid
from flask_cors import CORS
from datetime import datetime
import os
from time import perf_counter
import json
import requests
from typing import List
from skyfield.api import load as skyFieldLoad
from skyfield.positionlib import position_of_radec

# import logging

# logging.basicConfig(filename='app.log', filemode='w+', format='%(name)s - %(levelname)s - %(message)s')

# initialization
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['SECRET_KEY'] = os.environ['SPAM']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

CORS(app)
Markdown(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'])  #, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


class DictObject:
    def __init__(self, response):
        self.__dict__['_response'] = response

    def __getitem__(self, key):
        try:
            return self.__dict__['_response'][key]
        except KeyError:
            pass
        try:
            return self.__dict__[key]
        except KeyError:
            raise AttributeError(key)

    def __getattr__(self, key):
        # First, try to return from _response
        try:
            return self.__dict__['_response'][key]
        except KeyError:
            pass
        # If that fails, return default behavior so we don't break Python
        try:
            return self.__dict__[key]
        except KeyError:
            raise AttributeError(key)


@app.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(404, description="# missing arguments")
    if User.query.filter_by(username=username).first() is not None:
        abort(404, description="# existing user")
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


def load_json(path):
    if os.path.exists(path):
        with open(path) as json_file:
            return json.load(json_file)
    else:
        print('file not found')
        return {'result': None}


def save_json(new_json, path):
    with open(path, "w") as json_file:
        json.dump(new_json, json_file, indent=2)


def save_file(the_bytes, path):
    with open(path, "wb") as the_file:
        the_file.write(the_bytes)


config = DictObject(load_json('config.json'))
options = config.sat_options
data_store = load_json(config.data_store)




def data_store_merge(data: List):
    for i in data:
        if i['name'] not in data_store:
            data_store[i['name']] = i
        else:
            for k in i.keys():
                data_store[i['name']][k] = i[k]

    save_json(data_store, config.data_store)


def sort_repos(data_json):
    result = [
        {
            'name': repo['name'],
            'full_name': repo['full_name'],
            'updated': repo['updated_at'],
            'description': repo['description'],
            'html_url': repo['html_url']
        }
        for repo in data_json]

    result = sorted(result, key=lambda k: k['updated'])
    result.reverse()
    return result


def get_git_repository_update():
    repo_data_url = "https://api.github.com/users/luminome/repos"
    r = requests.get(repo_data_url, allow_redirects=True)
    json_res = r.content.decode('utf8').replace("'", '"')
    data = json.loads(json_res)
    data = sort_repos(data)
    save_json(data, config.data_path+'/git_projects.json')
    return data


def get_local_projects():
    loop_start = perf_counter()
    t_config = DictObject(load_json('config.json'))
    stash = []

    def local_projects():
        for root, dirs, files in os.walk(t_config.sites):
            for filename in files:
                omit = [x in root for x in t_config.sites_omitted_dirs]
                if True not in omit and 'readme.md' in filename.lower():
                    path = os.path.join(root, filename)
                    path_dir = os.path.basename(root)
                    t = os.path.getmtime(root)
                    d = datetime.fromtimestamp(t)
                    local_readme_path = config.source_path+'/'+path_dir+'.md'
                    stash.append(
                        {
                            "path": path,
                            "name": path_dir,
                            "updated": d.isoformat() + 'Z',
                            "local": local_readme_path,
                            "type": 'local'
                        }
                    )

    local_projects()
    data_store_merge(stash)

    for k in data_store.keys():
        if data_store[k] and data_store[k]['type'] == 'local':
            with open(data_store[k]['path'], "r") as the_file:
                save_file(bytes(the_file.read(), 'utf-8'), config.source_path+'/'+data_store[k]['name']+'.md')

    loop_stop = perf_counter()
    loop_time = "%.4fs" % (loop_stop - loop_start)

    return jsonify({'time': loop_time, 'result': stash})


@app.route('/update_repository_data')
def save_repository_data():
    def find_readme(item):
        for readme in ['readme', 'README']:
            readme_url = 'https://raw.githubusercontent.com/{}/master/{}.md'.format(item['full_name'], readme)
            r = requests.get(readme_url, allow_redirects=True)
            if b'404: Not Found' not in r.content:
                return r.content, readme_url
        return None, None

    data_abbr = get_git_repository_update()

    for abbr in data_abbr:
        abbr['type'] = 'remote'
        content, url = find_readme(abbr)
        if content is not None:
            abbr['url'] = url
            abbr['local'] = config.source_path+'/{}.md'.format(abbr['name'])
            save_file(content, abbr['local'])

    data_store_merge(data_abbr)
    # save_json(data_abbr, config.source_path + '/git_projects_info.json')

    return jsonify({'result': data_abbr})


@app.route('/data_store')
def get_data_store():
    return jsonify({'time': None, 'result': load_json(config.data_store)})


@app.route('/test')
def local_test():
    if 'localhost' in request.url_root:
        return get_local_projects()


@app.route('/load_external_configuration')
def external_test_gdrive():
    url = config.drive_conf_url
    r = requests.get(url, allow_redirects=True)
    print(r)
    with open(config.source_path+'/gdrive_projects_meta.json', 'wb') as gd_file:
        gd_file.write(r.content)

    return jsonify({'result': None})


@app.route('/sources')
def get_sources():
    loop_start = perf_counter()
    stash = []
    for root, dirs, files in os.walk(config.source_path):
        for filename in files:
            path = os.path.join(root, filename)
            t = os.path.getmtime(path)
            d = datetime.fromtimestamp(t)
            stash.append({
                "file": filename,
                "path": path,
                "updated": d.isoformat() + 'Z'
            })

    loop_stop = perf_counter()
    loop_time = "%.4fs" % (loop_stop - loop_start)

    return jsonify({'time': loop_time, 'result': stash})


# The actual decorator function
def require_api_key(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        key = os.environ['SPAM']
        #if request.args.get('key') and request.args.get('key') == key:
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == key:
            return view_function(*args, **kwargs)
        else:
            print("invalidated")
            abort(404, description="api_key missing or incorrect.")

    return decorated_function


@app.route('/io2/', methods=['GET'])
#@require_api_key
@auth.login_required
def get_io_two():
    return jsonify({'result': [{'msg': 'something posted'}], 'time': None})


@app.route('/io/', methods=['POST'])
#@require_api_key
@auth.login_required
def get_io():
    return jsonify({'result': [{'msg': 'something posted'}, request.json], 'time': None})


@app.route('/lsmft', methods=['GET'])
def lsmft():
#    print(request.request.environ)
    output = []
    for i, element in enumerate(request.environ.keys()):
        t = request.environ[element]
        if t.__class__ == str:
            print(element, t)
            output.append([element, t])

    return jsonify({'r': output})


@app.route('/', methods=['GET'])
def index():
    # if request.method == 'GET':

    data = load_json(config.data_store)
    files_array = []

    for i, element in enumerate(data.keys()):
        repo = data[element]

        if repo is not None:
            repo['id'] = str(i).zfill(2)
            k = {}

            for ke in repo.keys():
                if repo[ke] is not None:
                    k[ke] = repo[ke]

            if 'local' in repo:
                try:
                    with open(repo['local'], 'r') as file:
                        k['file'] = file.read()
                except FileNotFoundError:
                    k['file'] = 'no readme.md'
            else:
                k['file'] = 'no readme.md'

            files_array.append(k)

    #sort_repos(files_array)

    files_array = sorted(files_array, key=lambda k: k['updated'])
    files_array.reverse()

    header = {'root': request.url_root, 'id': 'hello'}
    return render_template('index.html', result=files_array, header=header)

    # else:
    #     k = os.environ['SPAM']
    #     if 'api_key' in request.json.keys():
    #         if request.json['api_key'] == k:
    #             request.json['api_key'] = 'collected'
    #
    #             return jsonify({'result': [{'msg': 'something posted'}, request.json], 'time': None})
    #



@app.route('/sat/<path:selection>', methods=['GET'])
def sat(selection):
    ts = skyFieldLoad.timescale()
    t = None

    if ':' in selection:
        selection, timestamp = selection.split(':')
        try:
            tt = [int(t) for t in timestamp.split('-')]
            t = ts.utc(tt[2], tt[0], tt[1], tt[3], tt[4], second=0.0)
            #utc(year, month=1, day=1, hour=0, minute=0, second=0.0)¶ from XXXX:1-17-2023-12-5
        except IndexError:
            abort(404, description="'{}' problem parsing time from {}".format(selection, timestamp))
    else:
        t = ts.now()

    if selection not in options:
        abort(404, description="'{}' resource doesn't have a record.".format(selection))

    loop_start = perf_counter()

    eph = skyFieldLoad('de421.bsp')

    if selection == 'iss':
        iss_id = 25544
        url = 'https://celestrak.org/NORAD/elements/gp.php?CATNR={}&FORMAT=tle'.format(iss_id)
        filename = 'tle-CATNR-{}.txt'.format(iss_id)
        satellites = skyFieldLoad.tle_file(url, filename=filename)
        element = satellites[0].at(t)
        so_type = element.__class__
        so_rpm = element.velocity.km_per_s
        so = element.subpoint()
    else:
        element = eph['earth'].at(t).observe(eph[selection])
        so_rpm = element.velocity.km_per_s
        so_type = element.__class__
        ast = element.apparent()
        ra, dec, distance = ast.radec()
        so = position_of_radec(ra.hours, dec.degrees, distance_au=distance.au, t=t, center=399).subpoint()

        # latitude,longitude,d = (ast.latitude,ast.longitude,ast.elevation)

    packet = {
        "latitude": round(so.latitude.degrees, 4),
        "longitude": round(so.longitude.degrees, 4),
        "elevation": round(so.elevation.km, 4),
        "km_per_sec": [round(e, 4) for e in so_rpm],
        "type": str(so_type)
    }

    loop_stop = perf_counter()
    loop_time = "%.4fs" % (loop_stop - loop_start)
    packet['path'] = selection
    packet['time'] = t.utc_strftime(format='%Y-%m-%d %H:%M:%S UTC')
    packet['exec_time'] = loop_time

    return jsonify(packet)


@app.route('/env')
def environment():
    print('wtf')
    r = request.url_root
    return jsonify({'r': r})
    #, 'os.env': dict(os.environ)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return jsonify({'error': str(e)})


def set_login_flare():
    now = datetime.now()
    ts = datetime.timestamp(now)
    token = jwt.encode(
        {"user_id": "admin", "t": ts},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    app.config["flare"] = token
    return token.decode('utf-8')




if __name__ == '__main__':
    #lsof -i :5000
    #format= '%(asctime)s-%(process)d-%(levelname)s-%(message)s'
    # logging.basicConfig(filename='app.log', filemode='w+', format='%(asctime)s-%(process)d-%(levelname)s-%(message)s')

    print("Creating PID file.")
    fh = open(config.data_path+"/app_process.pid", "w")
    fh.write(str(getpid()))
    fh.close()

    with app.app_context():
        if not os.path.exists('db.sqlite'):
            db.create_all()
        #test_connection(app)

    #handshake_send()


    app.run(debug=True, port=os.getenv("PORT", default=5000))
