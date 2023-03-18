# main.py

from flask import Blueprint, render_template, current_app, request, jsonify, redirect
from flask_login import login_required, current_user

from google_quick import gmail_init, gmail_certify
from .util import get_data_store_array, load_path

main = Blueprint('main', __name__)


@main.route('/quick')
def quick():
    return redirect(gmail_init())


@main.route('/connect/', methods=['GET'])
def quick_authorize():
    return redirect(gmail_certify(request.args))


@main.route('/')
def index():
    if current_app.config['run_config'].maintenance_mode == "True":
        return render_template('maintenance.html')
    else:
        header_data = load_path(current_app.config['run_config'].header_path)[1]
        index_components = get_data_store_array(current_app)[1]
        header = {'root': request.url_root, 'id': 'hello', 'content': header_data}
        return render_template('index.html', result=index_components, header=header)


@main.route('/admin/')
@login_required
def admin():
    requires_auth = current_app.config['run_config'].requires_auth == "True"
    has_cred = current_app.config['run_config'].has_credentials == "True"
    has_auth = current_app.config['run_config'].has_verification == "True"
    has_conf = current_app.config['run_config'].has_sent_confirm == "True"
    status = 'UserAuth:{} Credentialed:{}'.format(str(has_auth), str(has_cred))

    if requires_auth:
        if has_cred and not has_auth and not has_conf:
            return redirect(gmail_init())

        if not has_auth:
            return render_template('pre-admin.html', state=status)

    return render_template('admin.html', state=status)
