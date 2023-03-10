from flask import Flask, jsonify, abort, render_template, request
from flaskext.markdown import Markdown

from flask_cors import CORS

import os
from time import perf_counter
import json
import requests

from skyfield.api import load as skyFieldLoad
from skyfield.positionlib import position_of_radec


#https://raw.githubusercontent.com/luminome/ctipe-frontend/master/readme.md

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


# Flask(__name__, template_folder="static/templates")
CORS(app)
Markdown(app)

options = ['sun', 'moon', 'venus', 'mars', 'iss']


def sort_repos(data_json):
    result = [{'name': repo['name'], 'full_name': repo['full_name'], 'updated': repo['updated_at']} for repo in data_json]
    result = sorted(result, key=lambda k: k['updated'])
    result.reverse()
    return result


@app.route('/update_from_repos')
def get_git_user_update():
    repo_data_url = "https://api.github.com/users/luminome/repos"
    r = requests.get(repo_data_url, allow_redirects=True)
    json_res = r.content.decode('utf8').replace("'", '"')
    data = json.loads(json_res)
    with open('static/sources/git_repos.json', "w") as file:
        json.dump(data, file, indent=2)
    return jsonify(sort_repos(data))


@app.route('/get')
def get_data_from_user():
    # with open('user.json') as user_file:
    #     parsed_json = json.load(user_file)
    with open('static/sources/git_repos.json') as file:
        data = json.load(file)
        data_abbr = sort_repos(data)
        for abbr in data_abbr:
            url = 'https://raw.githubusercontent.com/{}/master/readme.md'.format(abbr['full_name'])
            abbr['url'] = url
            r = requests.get(url, allow_redirects=True)
            if b'404' not in r.content:
                abbr['local'] = 'static/sources/{}.md'.format(abbr['name'])
                with open(abbr['local'], 'wb') as md_file:
                    md_file.write(r.content)

        with open('static/sources/git_repos_shorthand.json', "w") as repo_file:
            json.dump(data_abbr, repo_file, indent=2)

        return jsonify({'result': data_abbr})


@app.route('/')
def index():
    # repo_data_url = "https://api.github.com/users/luminome/repos"
    # r = requests.get(repo_data_url, allow_redirects=True)
    #
    # url = 'https://raw.githubusercontent.com/luminome/ctipe-frontend/master/readme.md'
    # r = requests.get(url, allow_redirects=True)
    # open('static/sources/ctipe-frontend.md', 'wb').write(r.content)

    with open('static/sources/git_repos_shorthand.json') as file:
        data = json.load(file)

    files_array = []
    for repo in data:
        if 'local' in repo:
            with open(repo['local'], 'r') as file:
                files_array.append({'name': repo['name'], 'file': file.read()})

    #mkd_text = str(r.content)  #;//  #"## Your Markdown Here "
    return render_template('index.html', result=files_array)
    # return jsonify({"json": "hello-world python."})


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
    loop_time = "%.4fs" % (loop_stop-loop_start)
    packet['path'] = selection
    packet['time'] = t.utc_strftime(format='%Y-%m-%d %H:%M:%S UTC')
    packet['exec_time'] = loop_time

    return jsonify(packet)


@app.route('/env')
def environment():
    r = request.url_root
    return jsonify({'r': r, 'os.env': dict(os.environ)})


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
