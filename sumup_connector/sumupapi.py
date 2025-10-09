import logging
import json
import requests

logger = logging.getLogger(__name__)

FETCHLIMIT = 100

class SumupError(Exception):
    def __init__(self,r, message):
        super().__init__(message)
        self.json = { 'status_code': '000', 'message': str(message), 'reason': message }
        if r != None:
            self.json['url'] = r.url
            if r.reason:
                self.json['reason'] = str(r.reason)
            if r.status_code:
                self.json['status_code'] = r.status_code
        try:
           self.json['data'] = r.json()
           # some methods return an json with message,error_code 
           # as a json body on 50x and 50x. 
        except Except as e:
           pass

    def __str__(self):
        if 'data' in self.json and 'message' in self.json['data']:
             return self.json['data']['message']
        return self.reason
        
class SumupAPI():
  def __init__(self, merchant_code, api_key):
     self.API_KEY = api_key
     self.MERCHANT = merchant_code
     self.headers = {"Authorization": f"Bearer {self.API_KEY}"}
     self.URL = f'https://api.sumup.com/'

  def GET(self, path):
     url = self.URL + path
     try:
        r = requests.get(url,headers=self.headers)
        r.raise_for_status()
     except Exception as e:
        raise SumupError(r,e)
     return r.json()

  def POST(self, path, postdata):
     url = self.URL + path
     try:
        r = requests.post(url, json=postdata,headers=self.headers)
        r.raise_for_status()
     except Exception as e:
        return SumupError(r,e)
     return r.json()

  def list_readers(self):
     return self.GET(f'/v0.1/merchants/{self.MERCHANT}/readers')['items']


  def list_transactions(self, from_ref=None, changes_since=None):
     items = []
     qs = f'limit={FETCHLIMIT}&order=ascending&skip_tx_result=true'
     if from_ref != None:
         qs = qs + f"&oldest_ref={from_ref}"
     if changes_since != None:
         qs = qs + f"&changes_since={changes_since}"

     while True:
         r = self.GET(f'/v2.1/merchants/{self.MERCHANT}/transactions/history?{qs}')
         for t in r['items']:
            items.append(t)
         if not 'links' in r or r['links'][0]['rel'] != 'next':
              break
         qs = r['links'][0]['href']

     return items
