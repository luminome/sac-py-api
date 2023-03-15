# main.py

from flask import Blueprint, render_template, current_app, request
from flask_login import login_required, current_user

from .util import get_data_store_array

main = Blueprint('main', __name__)


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
    return render_template('admin.html', name=current_user.name)
