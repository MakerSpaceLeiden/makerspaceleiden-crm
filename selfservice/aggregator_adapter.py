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

    def _request_with_user_id(self, url, user_id):
        json_payload = {
            'user_id': user_id
        }
        req = urllib.request.Request(self.base_url + url,
                                     data=json.dumps(json_payload).encode('utf8'),
                                     headers={'Authorization': 'Basic %s' % self.encoded_credentials.decode("ascii")}
                                     )
        return urllib.request.urlopen(req).read().decode('utf-8')

    def generate_telegram_connect_token(self, user_id):
        token = self._request_with_user_id('/telegram/token', user_id)
        return token

    def disconnect_telegram(self, user_id):
        self._request_with_user_id('/telegram/disconnect', user_id)

    def onboard_signal(self, user_id):
        self._request_with_user_id('/signal/onboard', user_id)

    def notification_test(self, user_id):
        self._request_with_user_id('/notification/test', user_id)

    def checkout(self, user_id):
        self._request_with_user_id('/space/checkout', user_id)


def initialize_aggregator_adapter(base_url, username, password):
    handle['aggregator_adapter'] = AggregatorAdapter(base_url, username, password)


def get_aggregator_adapter():
    return handle['aggregator_adapter']
