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


def initialize_aggregator_adapter(base_url, username, password):
    handle['aggregator_adapter'] = AggregatorAdapter(base_url, username, password)


def get_aggregator_adapter():
    return handle['aggregator_adapter']
