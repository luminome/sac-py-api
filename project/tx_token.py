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
        "tx_token": the_tx_token,
        "tx": current_user.tx,
        "status": 1
    }
    return jsonify(carat)


@tx_token.route('/admin/', methods=['POST'])
@login_required
@auth.login_required
def admin():
    json_result = process_admin_cmd(current_app, request.json)
    return jsonify(json_result)