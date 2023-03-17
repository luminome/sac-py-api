# models.py

from flask import current_app
from flask_login import UserMixin
from passlib.apps import custom_app_context as pwd_context
from . import db

import jwt
import datetime
from datetime import timezone
import whatismyip

# class User(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
#     email = db.Column(db.String(100), unique=True)
#     password = db.Column(db.String(100))
#     name = db.Column(db.String(1000))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(32), index=True)
    password = db.Column(db.String(256))
    transaction_token = db.Column(db.String(256))
    tx = db.Column(db.Integer, default=0)

    def generate_transaction_token(self, expiration=60):
        now = datetime.datetime.now(tz=timezone.utc)
        ts = datetime.datetime.timestamp(now)

        payload = {
            "id": self.id,
            "user_id": "administrator",
            "user_pw": current_app.config['ADMIN_PASS'],
            "ip": whatismyip.whatismyipv4(),
            "t": ts,
            "tx": self.tx
        }

        if expiration != 0:
            payload['exp'] = now + datetime.timedelta(seconds=expiration)

        self.transaction_token = jwt.encode(
            payload,
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        #self.tx += 1
        return self.transaction_token
        #app.config["flare"] = token.decode('utf-8')

    @staticmethod
    def verify_transaction_token(token):
        try:
            transaction_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms="HS256")
        except jwt.InvalidSignatureError as error:
            return error
        except jwt.DecodeError as error:
            return error
        except jwt.ExpiredSignatureError as error:
            # user = User.query.get(app.config['GUID'])
            # user.tx = 0
            # user.generate_transaction_token()
            # return user
            # #
            # # # user.tx = 0
            # # # if token == app.config['FLARE']['token'].decode('utf-8'):
            # # # pick up where you left off...
            return error

        user = User.query.get(transaction_token['id'])
        if transaction_token['tx'] == user.tx:
            current_app.config['GUID'] = user.id
            #consume original transaction_token and make a new one
            user.tx += 1
            user.generate_transaction_token()
            return user
        else:
            return str('transaction token {} is no longer valid'.format(transaction_token['tx']))
