import base64
import json
import logging
import urllib.request

from django.apps import apps

logger = logging.getLogger(__name__)


class AggregatorAdapter(object):
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        credentials = "%s:%s" % (username, password)
        self.encoded_credentials = base64.b64encode(credentials.encode("ascii"))

    def fetch_state_space(self):
        url = self.base_url + "/space_state"
        req = urllib.request.Request(url)
        req.add_header(
            "Authorization", "Basic %s" % self.encoded_credentials.decode("ascii")
        )
        logger.debug("Fetching {} {}".format(req, url))
        return json.loads(urllib.request.urlopen(req).read())

    def _request_with_user_id(self, url, user_id=None):
        json_payload = {}
        if user_id is not None:
            json_payload["user_id"] = user_id
        try:
            url = self.base_url + url
            req = urllib.request.Request(
                url,
                data=json.dumps(json_payload).encode("utf8"),
                headers={
                    "Authorization": "Basic %s"
                    % self.encoded_credentials.decode("ascii")
                },
            )
            r = urllib.request.urlopen(req).read().decode("utf-8")
        except Exception as e:
            logger.error("Failed {} - {}".format(url, e))
            return None
        return r

    def generate_telegram_connect_token(self, user_id):
        token = self._request_with_user_id("/telegram/token", user_id)
        return token

    def disconnect_telegram(self, user_id):
        self._request_with_user_id("/telegram/disconnect", user_id)

    def onboard_signal(self, user_id):
        self._request_with_user_id("/signal/onboard", user_id)

    def checkout(self, user_id):
        self._request_with_user_id("/space/checkout", user_id)

    def get_chores(self):
        payload = self._request_with_user_id("/chores/overview")
        if payload:
            try:
                return json.loads(payload)
            except Exception:
                logger.error("Failed to parse the json chore: '{}'.".format(payload))
        return None


def initialize_aggregator_adapter(base_url, username, password):
    return AggregatorAdapter(base_url, username, password)


def get_aggregator_adapter():
    return apps.get_app_config("selfservice").aggregator_adapter
