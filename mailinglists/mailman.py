import urllib.request
import urllib.parse
import http.cookiejar
from lxml import html
import re

MAILMAN_URL = None # e.g. 'https://mailman.makerspaceleiden.nl/mailman'
MAILMAN_PASSWD = None # e.g. 'Foo'

# These should be "0" or "1" -- as a string.
#
LIST_OWNER_NOTIFS = "0"

class MailmanAlreadySubscribed(Exception):
    pass

class MailmanAccessNoSuchSubscriber(Exception):
    pass

class MailmanAccessDeniedException(Exception):
    pass

class MailmanException(Exception):
    pass

class MailmanService:
    CSRF_EXTRACT='//input[@name="csrf_token"]/@value[1]'

    def __init__(self, password = MAILMAN_PASSWD, adminurl = MAILMAN_URL):
        self.adminurl = adminurl
        self.password = password

        # Cookies and CSRF is valid across mailing lists. So we can keep these shared.
        #
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

        self.csrf_token = None
        
    def login(self, mailinglist ):
        url1 = f'{ self.adminurl }/admin/{ mailinglist }'
    
        # We may need this if the cookie is too old.
        # response = self.opener.open(url1)

        postdata = urllib.parse.urlencode({ 
                'adminpw': self.password
        }).encode('ascii')

        with self.opener.open(urllib.request.Request(url1, postdata)) as response:
                body = response.read()
                tree = html.fromstring(body)
                self.csrf_token = tree.xpath(self.CSRF_EXTRACT)[0]
                return True

        raise MailmanException("No CSRF/cookie available recived.")

    def post(self, mailinglist, url2, formparams):
        retry = True
        while(retry):
           try:
                 if not self.csrf_token:
                     self.login(mailinglist)
                     # We (re)try just once.
                     retry = False

                 formparams[ 'csrf_token' ] =  self.csrf_token
                 postdata = urllib.parse.urlencode(formparams).encode('ascii')
   
                 with self.opener.open(urllib.request.Request(url2, postdata)) as response:
                      body = response.read()
                      tree = html.fromstring(body)

                 if "The form lifetime has expire." not in str(body):
                          return body

           except urllib.error.HTTPError as e:
                   if e.code != 401:
                      raise e

           #propably a wrong cookie or CSRF issue; reset these. And try again.
           #
           self.csrf_token = None
           self.cj.clear()

        raise MailmanException("Unknown error")

class MailmanAccount:
    def __init__(self, service, mailinglist):
        self.service = service
        self.mailinglist = mailinglist

    def digest(self, email, onoff = None):
        if onoff == None:
              return self._option('digest', email)
        self._option('digest', email, onoff)

    def delivery(self, email, onoff = None):
        if onoff == None:
            return not self._option('disablemail', email)
        self._option('disablemail', email, not onoff)

    def subscribe(self, email, full_name = None):
        if full_name:
            email = f'{full_name} <{email}>'
        return self.mass_subscribe([email])

    def mass_subscribe(self,emails):
        url2 = f'{ self.service.adminurl }/admin/{self.mailinglist}/members/add'
        params = {
            'subscribe_or_invite': '0', # 0=subscribe, 1=invite
            'send_welcome_msg_to_this_batch': '0',
            'send_notifications_to_list_owner' : LIST_OWNER_NOTIFS,
            'subscribees': '\n'.join(emails),
            'invitation': '',
            'setmemberopts_btn': 'Submit Your Changes'
        }
        return self._adminform(url2, params)

    def unsubscribe(self,email):
        url2 = f'{ self.service.adminurl }/admin/{self.mailinglist}/members/remove'
        params = { 
           'send_unsub_ack_to_this_batch': "0", 
           'send_unsub_notifications_to_list_owner' : LIST_OWNER_NOTIFS,
           'unsubscribees': email,
           'setmemberopts_btn': 'Submit Your Changes'
        }
        return self._adminform(url2, params)

    def is_subscribed(self):
       try:
           d = self.delivery
           return True
       except MailmanAccessNoSuchSubscriber:
           pass
       return False

    def _option(self,field, email, onoff = None):
        if onoff != None:
           if onoff:
              onoff = "1"
           else:
              onoff = "0"

        params = {
            'options-submit':'Submit My Changes', # essential magic - gleaned from the ./Mailman/Cgi/options.py
            field: onoff 
        }
        email = re.sub('@','--at--',email)
        url2 = f'{ self.service.adminurl }/options/{self.mailinglist}/{email}'
        return self._adminform(url2, params)

    def _adminform(self, url2, params):
        print(f'HTTP get on {url2} -- {params}')
        return True

        # We prlly should intercepts CSRF at a handler
        # level - and hide it from subsequent calls. I.e.
        # make a CSRF OpenerDirector.
        #
        try:
   
           formparams = {}
           get = None
           for k,v in params.items():
               if v == None:
                  get = k
               else:
                  formparams[ k ] = v

           body = self.service.post(self.mailinglist, url2, formparams)
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
     service = MailmanService(password, adminurl)
     account = MailmanAccount(service, mlist, email)
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
