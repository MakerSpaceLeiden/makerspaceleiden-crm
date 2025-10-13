import logging

import requests
from moneyed import EUR

logger = logging.getLogger(__name__)

FETCHLIMIT = 100


class SumupError(Exception):
    def __init__(self, r, message):
        super().__init__(message)
        self.reason = str(message)
        try:
            self.json = {
                "status_code": "000",
                "message": str(message),
                "reason": message,
            }
        except Exception:
            self.json = {}
        if r is not None:
            self.json["url"] = r.url
            if r.status_code:
                self.json["status_code"] = r.status_code
        try:
            self.json["data"] = r.json()
            # some methods return an json with message,error_code
            # as a json body on 50x and 50x.
        except Exception:
            pass

    def __str__(self):
        if "data" in self.json and "message" in self.json["data"]:
            return self.json["data"]["message"]
        return self.reason


class SumupAPI:
    def __init__(self, merchant_code, api_key):
        self.API_KEY = api_key
        self.MERCHANT = merchant_code
        self.headers = {"Authorization": f"Bearer {self.API_KEY}"}
        self.URL = "https://api.sumup.com/"

    def GET(self, path):
        url = self.URL + path
        try:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise SumupError(r, e)
        return None

    def POST(self, path, postdata):
        url = self.URL + path
        r = None
        try:
            r = requests.post(url, json=postdata, headers=self.headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise SumupError(r, e)
        return None

    def list_readers(self):
        return self.GET(f"/v0.1/merchants/{self.MERCHANT}/readers")["items"]

    def list_transactions(self, from_ref=None, changes_since=None):
        items = []
        qs = f"limit={FETCHLIMIT}&order=ascending&skip_tx_result=true"
        if from_ref is not None:
            qs = qs + f"&oldest_ref={from_ref}"
        if changes_since is not None:
            qs = qs + f"&changes_since={changes_since}"

        while True:
            r = self.GET(f"/v2.1/merchants/{self.MERCHANT}/transactions/history?{qs}")
            for t in r["items"]:
                items.append(t)
            if "links" not in r or r["links"][0]["rel"] != "next":
                break
            qs = r["links"][0]["href"]

        return items

    def trigger_checkout(self, reader_id, amount, description, return_url):
        if amount.currency != EUR:
            raise Exception(f"Amount must be in EUROs, not {amount.currency}")
        json = self.POST(
            f"/v0.1/merchants/{self.MERCHANT}/readers/{reader_id}/checkout",
            {
                "description": description,
                "return_url": return_url,
                "tip_rates": [],
                "total_amount": {
                    "value": int(amount.amount * 100),
                    "currency": "EUR",
                    "minor_unit": 2,
                },
            },
        )
        return json["data"]
