import urllib
import json


class AggregatorAdapter(object):
    def __init__(self, base_url, username, password):
        self.base_url = base_url

        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.base_url, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        self.opener = urllib.request.build_opener(handler)

    def fetch_state_space(self):
        return json.loads(self.opener.open(self.base_url + '/space_state').read())

