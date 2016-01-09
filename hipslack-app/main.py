import flask
from flask.ext.sqlalchemy import SQLAlchemy
import json
import os
import requests
import time

__author__ = 'Bryson Tyrrell'
__email__ = "bryson.tyrrell@gmail.com"
__version__ = "1.0"


class Configuration(object):
    APPLICATION_DIR = os.path.dirname(os.path.realpath(__file__))
    INSTANCE_URL = 'your.hipslack.address'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/hipslack.db'.format(APPLICATION_DIR)
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SLACK_INCOMING_WEBHOOK_URL = 'https://hooks.slack.com/services/xxxxxxxxx/xxxxxxxxx/xxxxxxxxxxxxxxxxaxxxxxxx'
    SLACK_OUTGOING_WEBHOOK_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxx'

app = flask.Flask(__name__)
app.config.from_object(Configuration)

db = SQLAlchemy(app)

active_hipchat_tokens = {}


class InstanceModel(db.Model):
    hipchat_oauth_id = db.Column(db.String(36), primary_key=True)
    hipchat_oauth_secret = db.Column(db.String(40), unique=True)
    hipchat_room_id = db.Column(db.Integer)
    slack_incoming_webhook_url = db.Column(db.String())
    slack_outgoing_webhook_token = db.Column(db.String())

    def __init__(self, oauth_id, oauth_secret, room_id):
        self.hipchat_oauth_id = oauth_id
        self.hipchat_oauth_secret = oauth_secret
        self.hipchat_room_id = room_id
        self.slack_incoming_webhook_url = Configuration.SLACK_INCOMING_WEBHOOK_URL
        self.slack_outgoing_webhook_token = Configuration.SLACK_OUTGOING_WEBHOOK_TOKEN

    def __repr__(self):
        return "<OAuth: {}>".format(self.hipchat_oauth_id)


class HipChatToken(object):
    def __init__(self, oauthId, oauthSecret):
        self._oauthId = oauthId
        self._oauthSecret = oauthSecret
        self._token = None
        self._expires = None
        self.generate()

    def generate(self):
        print("generating new access token")
        data = {'grant_type': 'client_credentials', 'scope': 'send_notification'}
        headers = {'content-type': 'application/json'}
        response = requests.post('https://api.hipchat.com/v2/oauth/token', data=json.dumps(data), headers=headers,
                                 auth=(self._oauthId, self._oauthSecret))

        if response.status_code == 200:
            print('obtained new access token')
            token = response.json()
            expires = time.time() + token['expires_in']
            self._token = token['access_token']
            self._expires = expires
        else:
            print("unable to generate an access token: check the oauth id and secret")
            raise Exception

    def verify(self):
        now = time.time()
        if now >= self._expires:
            print("the access token has expired")
            self.generate()

    def __repr__(self):
        self.verify()
        return 'Bearer {0}'.format(self._token)


@app.route('/slack-incoming', methods=['POST'])
def slack_incoming_webhook():
    if not flask.request.form.get('bot_id'):
        token = flask.request.form.get('token')
        instance = InstanceModel.query.filter(InstanceModel.slack_outgoing_webhook_token == token).first_or_404()
        if instance:
            username = flask.request.form.get('user_name')
            message = flask.request.form.get('text')
            payload = {'from': '{} (via Slack)'.format(username), "color": 'gray', "message": message}
            headers = {'content-type': 'application/json', 'Authorization': active_hipchat_tokens[instance.hipchat_oauth_id]}
            response = requests.post('https://api.hipchat.com/v2/room/{}/notification'.format(instance.hipchat_room_id),
                                     data=json.dumps(payload), headers=headers)
            print response.text

    return '', 200


@app.route('/hipchat-incoming', methods=['POST'])
def hipchat_incoming_webhook():
    data = flask.request.get_json()
    if data['event'] == 'room_message':
        oauth_id = data['oauth_client_id']
        mention_name = data['item']['message']['from']['mention_name']
        mentions = data['item']['message']['mentions']
        message = data['item']['message']['message']

        payload = {
            'username': '{} (via HipChat)'.format(mention_name),
            'text': message
        }

        instance = InstanceModel.query.filter(InstanceModel.hipchat_oauth_id == oauth_id).first_or_404()
        requests.post(instance.slack_incoming_webhook_url, data=json.dumps(payload))

    return '', 200




@app.route('/hipchat-install', methods=['POST'])
def hipchat_install():
    data = flask.request.get_json()
    new_instance = InstanceModel(data['oauthId'], data['oauthSecret'], data['roomId'])
    db.session.add(new_instance)
    db.session.commit()
    active_hipchat_tokens[data['oauthId']] = HipChatToken(data['oauthId'], data['oauthSecret'])
    return '', 200


@app.route('/hipchat-capabilities')
def hipchat_capabilities():
    capabilities_data = {
        "name": "HipSlack",
        "key": "com.brysontyrrell.hipslack",
        "description": "Have a HipChat room and a Slack channel act as one.",
        "capabilities": {
            "installable": {
                "callbackUrl": "https://{}/hipchat-install".format(app.config['INSTANCE_URL']),
                "allowGlobal": False,
                "allowRoom": True
            },
            "hipchatApiConsumer": {
                "scopes": [
                    "send_notification"
                ],
                "fromName": "HipSlack"
            },
            "webhook": [
                {
                    "event": "room_message",
                    "url": "https://{}/hipchat-incoming".format(app.config['INSTANCE_URL'])
                }
            ]
        },
        "links": {
            "self": "https://{}/hipchat-capabilities".format(app.config['INSTANCE_URL'])
        }
    }
    return flask.jsonify(capabilities_data), 200


if __name__ == '__main__':
    installed_instances = InstanceModel.query.all()
    for installed_instance in installed_instances:
        active_hipchat_tokens[installed_instance.hipchat_oauth_id] = HipChatToken(installed_instance.hipchat_oauth_id,
                                                                                  installed_instance.hipchat_oauth_secret)

    app.run(host="0.0.0.0", port=443)
