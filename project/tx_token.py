# tx_token.py

from flask import Blueprint, abort, jsonify, request, current_app
from flask_login import login_required, current_user
from flask_httpauth import HTTPTokenAuth
from .models import User
from .util import process_admin_cmd

tx_token = Blueprint('tx_token', __name__)

auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token):
    response = User.verify_transaction_token(token)
    if response.__class__ is User:
        return response
    else:
        abort(503, description=response)


@tx_token.route('/acquire-transaction/', methods=['POST'])
@login_required
def start_transaction():
    the_tx_token = current_user.generate_transaction_token()
    carat = {
        "message": "Hello, {} attached is the requested tx_token".format(current_user.name),
        "tx_token": the_tx_token.decode('utf-8'),
        "tx": current_user.tx
    }

    print(carat)
    return jsonify(carat)


@tx_token.route('/admin/', methods=['POST'])
@login_required
@auth.login_required
def admin():
    mod_data = None
    mod_args = None

    if request.json['cmd'] == 'file_test':
        mod_data = bytes(request.json['b']).decode('utf-8')
    else:
        mod_data = request.json['cmd']

        if 'arg' in request.json:
            mod_args = request.json['arg']

        json_result = process_admin_cmd(mod_data, mod_args, current_app)
        return jsonify(json_result)

    carat = {
        # "message": "Hello, {}!".format(auth.current_user().name),
        # "tx_token": auth.current_user().transaction_token,
        # "tx": auth.current_user().tx,
        "data": mod_data
    }

    return jsonify(carat)



