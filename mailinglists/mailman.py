import urllib.request
import urllib.parse
import http.cookiejar
from lxml import html
import re

MAILMAN_URL = None # e.g. 'https://mailman.makerspaceleiden.nl/mailman'
MAILMAN_PASSWD = None # e.g. 'Foo'

class MailmanAlreadySubscribed(Exception):
    pass

class MailmanAccessNoSuchSubscriber(Exception):
    pass

class MailmanAccessDeniedException(Exception):
    pass

class MailmanException(Exception):
    pass

class MailmanAccount:
    CSRF_EXTRACT='//input[@name="csrf_token"]/@value[1]'
    FIELD_EXTRACT=''
    def __init__(self,mailinglist, email, password = MAILMAN_PASSWD, adminurl = MAILMAN_URL):
        self.adminurl = adminurl
        self.mailinglist = mailinglist
        self.email = email
        self.password = password

        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    @property
    def digest(self):
        return self._option('digest')

    @digest.setter
    def digest(self, onoff):
        self._option('digest', onoff)

    @property
    def delivery(self):
        return not self._option('disablemail')

    @delivery.setter
    def delivery(self, onof):
        self._option('disablemail', not onoff)

    def subscribe(self, email, full_name = None):
        if full_name:
            email = f'{full_name} <{email}>'
        return self.mass_subscribe([email])

    def mass_subscribe(self,emails):
        url2 = f'{ self.adminurl }/admin/{self.mailinglist}/members/add'
        params = {
            'subscribe_or_invite': '0', # 0=subscribe, 1=invite
            'send_welcome_msg_to_this_batch': '0',
            'send_notifications_to_list_owner' : '1',
            'subscribees': '\n'.join(emails),
            'invitation': '',
            'setmemberopts_btn': 'Submit Your Changes'
        }
        return self._adminform(url2, params)

    def unsubscribe(self, email):
        url2 = f'{ self.adminurl }/admin/{self.mailinglist}/members/remove'
        params = { 
           'send_unsub_ack_to_this_batch': "0", 
           'send_unsub_notifications_to_list_owner' : '1',
           'unsubscribees': email,
           'setmemberopts_btn': 'Submit Your Changes'
        }
        return self._adminform(url2, params)

    def _option(self,field, onoff = None):
        if onoff != None:
           if onoff:
              onoff = "1"
           else:
              onoff = "0"

        params = {
            'options-submit':'Submit My Changes', # essential magic - gleaned from the ./Mailman/Cgi/options.py
            field: onoff 
        }
        url2 = f'{ self.adminurl }/options/{self.mailinglist}/{email}'
        return self._adminform(url2, params)

    def _adminform(self, url2, params):
        # We prlly should intercepts CSRF at a handler
        # level - and hide it from subsequent calls. I.e.
        # make a CSRF OpenerDirector.
        #
        try:
           re.sub('@','--at--',self.email)
           url1 = f'{ self.adminurl }/admin/{ self.mailinglist }'
    
           # We may need this if the cookie is too old.
           # response = self.opener.open(url1)

           postdata = urllib.parse.urlencode({ 
                'adminpw': self.password
           }).encode('ascii')

           with self.opener.open(urllib.request.Request(url1, postdata)) as response:
                body = response.read()
                tree = html.fromstring(body)
                csrf_token = tree.xpath(self.CSRF_EXTRACT)[0]
   
           formparams = {}
           get = None
           for k,v in params.items():
               if v == None:
                  get = k
               else:
                  formparams[ k ] = v
            
           formparams[ 'csrf_token' ] =  csrf_token
           postdata = urllib.parse.urlencode(formparams).encode('ascii')

           with self.opener.open(urllib.request.Request(url2, postdata)) as response:
                body = response.read()
                tree = html.fromstring(body)

           # bit of a hack - should be a chat/expect per form type. But these
           # are unique enough for the few functons that we have.
           if 'Already a member' in str(body):
               raise MailmanAlreadySubscribed("already a member")

           if 'Successfully subscribed:' in str(body):
               return True

           if 'Successfully Unsubscribed:' in str(body):
               return True

           if 'Cannot unsubscribe non-members:' in str(body):
                raise MailmanAccessNoSuchSubscriber("not found")

           if 'mailing list membership configuration for' not in str(body):
                raise MailmanAccessNoSuchSubscriber("not found")

           if get:
                val = tree.xpath('//input[@name="'+get+'" and @checked]/@value')[0]
                if str(val) == "0":
                       return False
                if str(val) == "1":
                       return True
                raise MailmanException(f"Could not retrieve {field} settings.")

           results = {}
           for k,v in params.items():
               val = tree.xpath('//input[@name="'+get+'" and @checked]/@value')[0]
               results[ k ] = str(val)

           return results

        except urllib.error.HTTPError as e:
            if e.code == 401:
                    raise MailmanAccessDeniedException(f"Access denied")
            raise e

        raise MailmanException(f"Failed to set {field}.")

import sys

if __name__ == "__main__":
   (what,adminurl, mlist,email,password) = sys.argv[1:]
   try:
     account = MailmanAccount(mlist, email, password, adminurl)
     if what == 'info':
       print(f'Delivery: { account.delivery }')
       print(f'Digest:   { account.digest }')
     elif what == 'sub':
       print(account.subscribe(email))
     elif what == 'unsub':
       print(account.unsubscribe(email))
     else:
       print("Eh - just now info, sub and ubsub") 
   except MailmanAccessDeniedException as e:
     print("Access denied")
   except MailmanAccessNoSuchSubscriber:
     print("That emailis not on this list.")
