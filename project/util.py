import os
import json
from time import perf_counter

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


def pre_configure():
    root_path = os.path.abspath(os.curdir)
    conf_path = 'config-local.json'  #os.path.join(root_path, 'config-local.json')

    if os.path.exists(conf_path):
        with open(conf_path) as json_file:
            config = DictObject(json.load(json_file))
            os.environ['SPAM_ADMIN_MAIL'] = config.mail
            os.environ['SPAM_ADMIN_PASS'] = config.pass_cred
            os.environ['SPAM'] = config.key

    conf_path = 'config.json'  #os.path.join(root_path, 'config.json')
    with open(conf_path) as json_file:
        config = DictObject(json.load(json_file))
        config.root_path = root_path
        return config


def load_json(path):
    json_path = path
    if os.path.exists(json_path):
        with open(json_path) as json_file:
            return json.load(json_file)
    else:
        print(path, 'path doesn\'t exist')
        return {'result': None}


def save_json(new_json, path):
    with open(path, "w") as json_file:
        json.dump(new_json, json_file, indent=2)


def save_file(the_bytes, path):
    with open(path, "wb") as the_file:
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

    return True


def get_data_store(app, args=None):
    return app.config['DATA_STORE']


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

    return result


def configure(app, args=None):
    print(args)
    if args:
        k_v = args.split(':')
        conf = app.config['run_config']
        conf[k_v[0]] = k_v[1]
        return {'message': 'configuration changed; {} was set to {}'.format(k_v[0], k_v[1])}

    return None


cmd_table = {
    "update_repository_data": None,
    "get_data_store": None,
    "get_data_store_array": None,
    "configure": None
}


def process_admin_cmd(cmd_str: str, arg_str: str, app):
    loop_start = perf_counter()
    #print(cmd_str, arg_str)
    if cmd_str in cmd_table:
        el = globals()[cmd_str](app, arg_str)

        loop_stop = perf_counter()
        loop_time = "%.4fs" % (loop_stop - loop_start)
        return {'message': 'cmd:{} args:{}'.format(cmd_str, arg_str), 'data': el, 'time': loop_time}
