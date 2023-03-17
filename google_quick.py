from __future__ import print_function
import base64
from email.message import EmailMessage

import os
from flask import current_app
# from Google import Create_Service
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build


SCOPES = ['https://mail.google.com/']
CRED_PATH = 'expectations.json'


def gmail_init():
    BASE_URI = os.environ['BASE_URI']

    try:
        flow = Flow.from_client_secrets_file(
            CRED_PATH,
            scopes=SCOPES)
    except (FileNotFoundError, ValueError):
        return '/'

    flow.redirect_uri = BASE_URI+'connect/'

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    return authorization_url


def gmail_certify(args):
    from project.util import get_antigen
    BASE_URI = os.environ['BASE_URI']

    try:
        flow = Flow.from_client_secrets_file(
            CRED_PATH,
            scopes=SCOPES)
    except (FileNotFoundError, ValueError):
        return '/'

    flow.redirect_uri = BASE_URI+'connect/'
    flow.fetch_token(code=args['code'], state=args['state'], scope=args['scope'])
    creds = flow.credentials

    service = build('gmail', 'v1', credentials=creds)
    message = EmailMessage()

    message.set_content('This is automated draft mail. \n\n{}'.format(get_antigen()))

    message['To'] = 'sac.673@gmail.com'
    message['From'] = 'sac.673@gmail.com'
    message['Subject'] = 'sac-py-api credentials'

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {
        'raw': encoded_message
    }

    # pylint: disable=E1101
    send_message = (service.users().messages().send
                    (userId="me", body=create_message).execute())

    print(F'Message Id: {send_message["id"]}')

    current_app.config['run_config'].has_credentials = "True"
    current_app.config['run_config'].has_sent_confirm = "True"
    #return send_message

    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    return BASE_URI+'admin/'
