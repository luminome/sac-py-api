# public_api.py

from flask import Blueprint, jsonify, abort
from skyfield.api import load as sky_field_load
from skyfield.positionlib import position_of_radec
from time import perf_counter
from . import config

public_api = Blueprint('public_api', __name__)


@public_api.route('/sat/<path:selection>', methods=['GET'])
def sat(selection):
    ts = sky_field_load.timescale()
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

    if selection not in config.sat_options:
        abort(404, description="'{}' resource doesn't have a record.".format(selection))

    loop_start = perf_counter()

    eph = sky_field_load('de421.bsp')

    if selection == 'iss':
        iss_id = 25544
        url = 'https://celestrak.org/NORAD/elements/gp.php?CATNR={}&FORMAT=tle'.format(iss_id)
        filename = 'tle-CATNR-{}.txt'.format(iss_id)
        satellites = sky_field_load.tle_file(url, filename=filename)
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

