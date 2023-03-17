# main.py

from flask import Blueprint, render_template, current_app, request, jsonify, redirect
from flask_login import login_required, current_user

from google_quick import gmail_init, gmail_certify
from .util import get_data_store_array

main = Blueprint('main', __name__)


@main.route('/quick')
def quick():
    authorization_url = gmail_init()
    return redirect(authorization_url)


@main.route('/connect/', methods=['GET'])
def quick_authorize():
    result = gmail_certify(request.args)
    return redirect(result)


@main.route('/')
def index():
    if current_app.config['run_config'].maintenance_mode == "True":
        return render_template('maintenance.html')
    else:
        index_components = get_data_store_array(current_app)
        header = {'root': request.url_root, 'id': 'hello'}
        return render_template('index.html', result=index_components, header=header)
        #return render_template('index.html')


@main.route('/admin/')
@login_required
def admin():
    status = 'UserAuth:{} Credentialed:{}'.format(
        current_app.config['run_config'].has_verification,
        current_app.config['run_config'].has_credentials
    )

    if current_app.config['run_config'].has_credentials == "True" and current_app.config['run_config'].has_verification == "False":
        if current_app.config['run_config'].has_sent_confirm == "False":
            # send email for confirm.
            return quick()
            # go collect your email
            pass

    if current_app.config['run_config'].has_verification == "False":
        return render_template('pre-admin.html', name=current_user.name, state=status)
    else:
        return render_template('admin.html', name=current_user.name, state=current_app.config['run_config'].has_verification)
