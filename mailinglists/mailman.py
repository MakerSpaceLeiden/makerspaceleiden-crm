import urllib.request
import urllib.parse
import http.cookiejar
from lxml import html
import re


# MAILMAN_URL='https://mailman.makerspaceleiden.nl/mailman'
# LIST='spacelog'
# MAILMAN_PASSWD='...'

class MailmanException(Exception):
    pass

class MailmanAccount:
    CSRF_EXTRACT='//input[@name="csrf_token"]/@value[1]'
    FIELD_EXTRACT=''
    def __init__(self,adminurl, mailinglist, email):
        self.adminurl = adminurl
        self.mailinglist = mailinglist
        self.email = email

        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    @property
    def digest(self):
        return self._adminform('digest')


    @digest.setter
    def digest(self, onoff):
        self._adminform('digest', onoff)

    @property
    def delivery(self):
        return not self._adminform('disablemail')

    @delivery.setter
    def delivery(self, onof):
        self._adminform('disablemail', not onoff)

    def subscribe(self, email, full_name = None):
        if full_name:
            email = f'{full_name} <{email}>'
        return self.mass_subscribe([email])

    def mass_subscribe(self,emails):
        URL='admin/spacelog/members/add '
        fields = [ 
            'subscribe_or_invite': '0', # 0=subscribe, 1=invite
            'send_welcome_msg_to_this_batch': '0',
            'send_notifications_to_list_owner' : '1',
            'subscribees': '\n'.join(emails),
            'invitation': 'Some inviation text.',
            'setmemberopts_btn': 'Submit Your Changes'

    def unsubscribe(self, email):
        ULRL = 'admin/spacelog/members/remove '
        fields = { 
           'send_unsub_ack_to_this_batch': "0", 
           'send_unsub_notifications_to_list_owner' : '1',
           'unsubscribees': "\n".join(email),
           'setmemberopts_btn' = 'Submit Your Changes'
        }

    def _option(field, onoff = None):
        parans = {
            'options-submit':'Submit My Changes', # essential magic - gleaned from the ./Mailman/Cgi/options.py
            field: onoff 
        }
        return self._adminform(params)

    def _adminform(params):
        # We prlly should intercepts CSRF at a handler
        # level - and hide it from subsequent calls. I.e.
        # make a CSRF OpenerDirector.
        #
        try:
           re.sub('@','--at--',self.email)
           url1 = f'{ MAILMAN_URL }/admin/{ self.mailinglist }'
           url2 = f'{ MAILMAN_URL}/options/{self.mailinglist}/{email}'
    
           # We may need this if the cookie is too old.
           # response = self.opener.open(url1)

           postdata = urllib.parse.urlencode({ 
                'adminpw': MAILMAN_PASSWD 
           }).encode('ascii')

           with self.opener.open(urllib.request.Request(url1, postdata)) as response:
                body = response.read()
                tree = html.fromstring(body)
                csrf_token = tree.xpath(CSRF_EXTRACT)[0]
     
           if onoff == None:
                postdata = None
           else:
                if onoff:
                    onoff = "1"
                else:
                    onoff = "0"

                params[ 'csrf_token' ] =  csrf_token
                postdata = urllib.parse.urlencode(params).encode('ascii')
             
           with self.opener.open(urllib.request.Request(url2, postdata)) as response:
                body = response.read()
                tree = html.fromstring(body)
                onoff_new = tree.xpath('//input[@name="'+field+'" and @checked]/@value')[0]

           if onoff == None:
                  if str(onoff_new) == "0":
                       return False
                  if str(onoff_new) == "1":
                       return True
                  raise MailmanException(f"Could not retrieve {field} settings.")

           if int(onoff_new) == int(onoff):
                return digest

        except urllib.error.HTTPError as e:
            if e.code == 401:
                    raise MailmanException(f"Access denied")
            raise e

        raise MailmanException(f"Failed to set {field}.")
