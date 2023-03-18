# init.py

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flaskext.markdown import Markdown

from werkzeug.security import generate_password_hash
from .util import DictObject, pre_configure, load_json


# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

#check if locally configured environment
config = pre_configure()


def create_app():
    app = Flask(__name__, static_url_path='', static_folder='../static')
    CORS(app)
    Markdown(app)

    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['SECRET_KEY'] = os.environ['SPAM']
    app.config['ADMIN_MAIL'] = os.environ['SPAM_ADMIN_MAIL']
    app.config['ADMIN_PASS'] = os.environ['SPAM_ADMIN_PASS']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    app.config['INIT'] = False
    message, app.config['DATA_STORE'], status = load_json(config.data_store_path)

    app.config['run_config'] = config
    db.init_app(app)

    with open(config.data_path + "/app_process.pid", "w") as pid_file:
        pid = str(os.getpid())
        app.config["SECRET_SPID"] = pid
        pid_file.write(pid)
        print('process_id saved [{}]'.format(pid))

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    with app.app_context():
        db.drop_all()
        db.create_all()

        email = app.config['ADMIN_MAIL']
        name = 'SAC-Administrator'
        password = app.config['ADMIN_PASS']
        # create new user with the form data. Hash the password so plaintext version isn't saved.
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for public_api of app
    from .public_api import public_api as public_api_blueprint
    app.register_blueprint(public_api_blueprint)

    # blueprint for tx_routes of app
    from .tx_token import tx_token as tx_token_blueprint
    app.register_blueprint(tx_token_blueprint)

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return jsonify({'error': str(e)})

    @app.errorhandler(503)
    def token_malfunction(e):
        # note that we set the 404 status explicitly
        return jsonify({'error': str(e)})



    return app
