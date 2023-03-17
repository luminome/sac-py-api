# tx_token.py
import json

from flask import Blueprint, abort, jsonify, request, current_app, redirect
from flask_login import login_required, current_user
from flask_httpauth import HTTPTokenAuth
from .models import User
from .util import process_admin_cmd, save_json
from google_quick import gmail_init
import datetime
from datetime import timezone

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

    if request.json['cmd'] == 'expectations':
        if request.json['b']:
            if current_app.config['run_config'].has_credentials == "False":
                mod_data = bytes(request.json['b'])
                #save the expectations mod_data for login
                try:
                    valid_json = json.loads(mod_data)
                    if 'web' in valid_json:
                        save_json(valid_json, 'expectations.json')
                        confirm = '<a href="{}">initialize expectations and send</a>'.format(gmail_init())
                        mod_data = "saved and loaded json expectations."
                        return jsonify({'confirm': confirm, 'message': mod_data})
                    else:
                        mod_data = "cannot be valid expectations"

                except json.JSONDecodeError as error:
                    mod_data = str(error)

        if current_app.config['run_config'].has_credentials == "True" and request.json['b'] is not None:
            mod_data = bytes(request.json['b']).decode('utf-8')
            if mod_data == current_app.config['run_config'].master_auth:
                print("here's the final stage for compare..")
                current_app.config['run_config'].has_verification = "True"
                confirm = '<a href="{}">credential accepted, proceed to admin</a>'.format('/admin/')
                return jsonify({'confirm': confirm})

    elif request.json['cmd'] == 'file':
        mod_data = bytes(request.json['b']).decode('utf-8')

    else:
        mod_data = request.json['cmd']

        if 'arg' in request.json:
            mod_args = request.json['arg']

        json_result = process_admin_cmd(mod_data, mod_args, current_app)
        return jsonify(json_result)

    carat = {
        "data": mod_data
    }

    return jsonify(carat)



