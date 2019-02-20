import urllib.request
import base64
import json


handle = {
    'aggregator_adapter': None,
}


class AggregatorAdapter(object):
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        credentials = ('%s:%s' % (username, password))
        self.encoded_credentials = base64.b64encode(credentials.encode('ascii'))

    def fetch_state_space(self):
        req = urllib.request.Request(self.base_url + '/space_state')
        req.add_header('Authorization', 'Basic %s' % self.encoded_credentials.decode("ascii"))
        return json.loads(urllib.request.urlopen(req).read())

    def generate_telegram_connect_token(self, user_id):
        json_payload = {
            'user_id': user_id
        }
        req = urllib.request.Request(self.base_url + '/telegram/token',
                                     data=json.dumps(json_payload).encode('utf8'),
                                     headers={'Authorization': 'Basic %s' % self.encoded_credentials.decode("ascii")}
                                     )
        token = urllib.request.urlopen(req).read().decode('utf-8')
        return token

    def disconnect_telegram(self, user_id):
        json_payload = {
            'user_id': user_id
        }
        req = urllib.request.Request(self.base_url + '/telegram/disconnect',
                                     data=json.dumps(json_payload).encode('utf8'),
                                     headers={'Authorization': 'Basic %s' % self.encoded_credentials.decode("ascii")}
                                     )
        urllib.request.urlopen(req).read().decode('utf-8')

    def onboard_signal(self, user_id):
        json_payload = {
            'user_id': user_id
        }
        req = urllib.request.Request(self.base_url + '/signal/onboard',
                                     data=json.dumps(json_payload).encode('utf8'),
                                     headers={'Authorization': 'Basic %s' % self.encoded_credentials.decode("ascii")}
                                     )
        urllib.request.urlopen(req).read().decode('utf-8')

    def notification_test(self, user_id):
        json_payload = {
            'user_id': user_id
        }
        req = urllib.request.Request(self.base_url + '/notification/test',
                                     data=json.dumps(json_payload).encode('utf8'),
                                     headers={'Authorization': 'Basic %s' % self.encoded_credentials.decode("ascii")}
                                     )
        urllib.request.urlopen(req).read().decode('utf-8')


def initialize_aggregator_adapter(base_url, username, password):
    handle['aggregator_adapter'] = AggregatorAdapter(base_url, username, password)


def get_aggregator_adapter():
    return handle['aggregator_adapter']
