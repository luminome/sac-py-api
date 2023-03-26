import os
import json
from time import perf_counter
# from google_quick import gmail_init
import datetime
from datetime import timezone
from werkzeug.security import generate_password_hash
from flask import current_app
from google_quick import gmail_init


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

    def __setitem__(self, key, value):
        self.__dict__['_response'][key] = value

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


def get_antigen() -> str:
    now = datetime.datetime.now(tz=timezone.utc)
    ts = datetime.datetime.timestamp(now)
    antigen = generate_password_hash(str(ts), method='sha256')
    current_app.config['run_config'].master_auth = antigen
    return antigen


def pre_configure():
    root_path = os.path.abspath(os.curdir)
    conf_path = 'config-local.json'  #os.path.join(root_path, 'config-local.json')

    if os.path.exists(conf_path):
        with open(conf_path) as json_file:
            config = DictObject(json.load(json_file))
            os.environ['SPAM_ADMIN_MAIL'] = config.mail
            os.environ['SPAM_ADMIN_PASS'] = config.pass_cred
            os.environ['SPAM'] = config.key
            os.environ['BASE_URI'] = config.base

    conf_path = 'config.json'  #os.path.join(root_path, 'config.json')
    with open(conf_path) as json_file:
        config = DictObject(json.load(json_file))
        config.root_path = root_path
        return config


def load_json(path):
    json_path = path
    if os.path.exists(json_path):
        with open(json_path) as json_file:
            return 'ok', json.load(json_file), 1
    else:
        return '({}) path doesn\'t exist'.format(path), None, 0


def load_path(path):
    if os.path.exists(path):
        with open(path, 'r') as _file:
            return 'ok', _file.read(), 1
    return '({}) path doesn\'t exist'.format(path), None, 0


def save_json(new_json, path):
    with open(path, "w") as json_file:
        json.dump(new_json, json_file, indent=2)


def save_file(the_bytes, path):
    with open(path, "wb+") as the_file:
        the_file.write(the_bytes)


def update_repository_data(app, nid=None):
    import requests

    def find_readme(item):
        for readme in ['readme', 'README']:
            readme_url = 'https://raw.githubusercontent.com/{}/master/{}.md'.format(item['full_name'], readme)
            r = requests.get(readme_url, allow_redirects=True)
            if b'404: Not Found' not in r.content:
                return r.content, readme_url
        return None, None

    repo_data_url = "https://api.github.com/users/luminome/repos"
    r = requests.get(repo_data_url, allow_redirects=True)
    json_res = r.content.decode('utf8').replace("'", '"')
    data = json.loads(json_res)

    for abbr in data:
        abbr['type'] = 'remote'
        content, url = find_readme(abbr)
        if content is not None:
            abbr['url'] = url
            abbr['local'] = app.config['run_config'].source_path+'/{}.md'.format(abbr['name'])
            save_file(content, abbr['local'])

    return 'processed {} files'.format(len(data)), {'path': app.config['run_config'].source_path}, 1


def get_data_store(app, args=None):
    path = app.config['run_config'].data_store_path
    message, ref, status = load_json(path)
    return 'ok', {'path': path, 'file-body': ref}, 1


def get_file_path(app, args=None):
    message, ref, status = load_path(args['path'])
    return message, {'path': args['path'], 'file-body': ref}, status


def put_file_path(app, args=None):
    message = 'no source'
    response = None
    save_able = None
    path = None

    if 'path' in args and args['path'] is not None:
        if os.path.exists(args['path']):
            path = args['path']
            save_able = True
        if os.path.exists(os.path.dirname(args['path'])):
            path = args['path']
            save_able = True

    if 'payload' in args and args['payload'] is not None:
        if save_able:
            data = bytes(args['payload'])
            save_file(data, path)
            data = load_path(args['path'])[1]
            message = '{} file-saved.'.format(path)
        else:
            data = bytes(args['payload']).decode('utf-8')
            message = '{} file-transited path invalid.'.format(args['path'])

        response = {'file-body': data, 'path': path}

    return message, response, 1


def get_data_store_array(app, args=None):
    data = app.config['DATA_STORE']
    projects = []

    for i, element in enumerate(data.keys()):
        projects.append(data[element])

    result = sorted(projects, key=lambda k: k['updated'])
    result.reverse()

    for i, repo in enumerate(result):
        repo['id'] = str(i).zfill(2)
        if 'local' in repo:
            try:
                with open(repo['local'], 'r') as file:
                    repo['file'] = file.read()
            except FileNotFoundError:
                repo['file'] = 'no readme.md'
        else:
            repo['file'] = 'no readme.md'

    return 'all data', result, 1


def configure(app, args=None):
    if 'value' in args:
        k_v = args['value'].split(':')
        conf = app.config['run_config']
        conf[k_v[0]] = k_v[1]
        return 'configuration changed; {} was set to {}'.format(k_v[0], k_v[1]), None, 1

    return 'no configuration available', None, 0


def expectations(app, args=None):
    message = 'default expectations no payload'
    output_data = {}
    h_cred = app.config['run_config'].has_credentials == "True"
    status = 0

    if 'payload' in args and args['payload'] is not None:
        if not h_cred:
            data = bytes(args['payload'])
            print("validating payload")
            try:
                valid_json = json.loads(data)
                if 'web' in valid_json:
                    save_json(valid_json, 'expectations.json')
                    app.config['run_config'].has_credentials = "True"
                    output_data['link'] = '<a href="{}">initialize expectations and send</a>'.format(gmail_init())
                    message = "saved and loaded json expectations."
                    status = 1
                else:
                    message = "cannot be valid expectations"

            except json.JSONDecodeError as error:
                message = 'invalid: {}'.format(str(error))

        if h_cred:
            data = bytes(args['payload']).decode('utf-8')
            if data == app.config['run_config'].master_auth:
                app.config['run_config'].has_verification = "True"
                output_data['link'] = '<a href="{}">credential accepted, proceed to admin</a>'.format('/admin/')
                message = "expectations verified"
                status = 1
            else:
                message = "expectation antigen not verified"

    return message, output_data, status


cmd_table = {
    "update_repository_data": None,
    "get_data_store": None,
    "get_data_store_array": None,
    "get_file_path": None,
    "put_file_path": None,
    "expectations": None,
    "configure": None
}


def process_admin_cmd(app, args: json):
    loop_start = perf_counter()
    message = None
    status = 0
    datum = None

    if args['cmd'] in cmd_table:
        message, datum, status = globals()[args['cmd']](app, args['arg'])

    loop_stop = perf_counter()
    loop_time = "%.4fs" % (loop_stop - loop_start)
    return {'message': message, 'command': args['cmd'], 'data': datum, 'time': loop_time, 'status': status}
