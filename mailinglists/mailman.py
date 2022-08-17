import urllib.request
import urllib.parse
import http.cookiejar
from lxml import html
import re

import logging

logger = logging.getLogger(__name__)

MAILMAN_URL = None  # e.g. 'https://mailman.makerspaceleiden.nl/mailman'
MAILMAN_PASSWD = None  # e.g. 'Foo'

# These should be "0" or "1" -- as a string.
#
LIST_OWNER_NOTIFS = "1"


class MailmanAlreadySubscribed(Exception):
    pass


class MailmanAccessNoSuchSubscriber(Exception):
    pass


class MailmanAccessDeniedException(Exception):
    pass

class MailmanAccessLoginFail(Exception):
    pass

class MailmanException(Exception):
    pass


class MailmanService:
    CSRF_EXTRACT = '//input[@name="csrf_token"]/@value[1]'

    def __init__(self, password=MAILMAN_PASSWD, adminurl=MAILMAN_URL):
        self.adminurl = adminurl
        self.password = password

        # Cookies and CSRF is valid across mailing lists. So we can keep these shared.
        #
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )

        self.csrf_token = None

    def __str__(self):
        return f"MailmanService-{MailmanService}"

    def login(self, mailinglist):
        url1 = f"{ self.adminurl }/admin/{ mailinglist }"
        # We may need this if the cookie is too old.
        # response = self.opener.open(url1)

        postdata = urllib.parse.urlencode({"adminpw": self.password}).encode("ascii")

        logger.info(f"LOGIN {url1}")
        with self.opener.open(urllib.request.Request(url1, postdata)) as response:
            body = response.read()
            tree = html.fromstring(body)
            self.csrf_token = tree.xpath(self.CSRF_EXTRACT)[0]
            if self.csrf_token:
                # print(self.csrf_token)
                return True
        raise MailmanException("No CSRF/cookie available recived.")

    def post(self, mailinglist, url2, formparams):
        retry = True
        while retry:
            try:
                if not self.csrf_token:
                    # We (re)try just once.
                    retry = False
                    self.login(mailinglist)

                formparams["csrf_token"] = self.csrf_token
                postdata = urllib.parse.urlencode(formparams).encode("ascii")
                logger.info(f"POST {url2}")
                with self.opener.open(
                    urllib.request.Request(url2, postdata)
                ) as response:
                    body = response.read()
                    tree = html.fromstring(body)

                if "first log in by giving your" in str(body):
                   if not retry:
                       raise MailmanAccessLoginFail
                   logger.info("Re-logign in")
                   self.login(mailinglist)

                if "The form lifetime has expire." not in str(
                    body
                ) and "List Administrator Password:" not in str(body):
                    return body

            except urllib.error.HTTPError as e:
                if e.code != 401:
                    raise e

            # propably a wrong cookie or CSRF issue; reset these. And try again.
            #
            self.csrf_token = None
            self.cj.clear()

        raise MailmanException("Unknown error - e.g. wrong password - POST")

    def get(self, mailinglist, path):
        url = f"{ self.adminurl }/{ path }"
        retry = True
        while retry:
            try:
                if not self.csrf_token:
                    retry = False
                    self.login(mailinglist)
                return self.opener.open(urllib.request.Request(url))

            except urllib.error.HTTPError as e:
                if e.code != 401:
                    logger.error(f"Mailinglist proxy get on url {url} failed.")
                    raise e

            # propably a wrong cookie or CSRF issue; reset these. And try again.
            #
            self.csrf_token = None
            self.cj.clear()

        raise MailmanException("Unknown error - e.g. wrong password - GET")


class MailmanAccount:
    def __init__(self, service, mailinglist):
        self.service = service
        self.mailinglist = mailinglist

    def digest(self, email, onoff=None):
        if onoff == None:
            return self._option("digest", email)
        self._option("digest", email, onoff)

    def delivery(self, email, onoff=None):
        if onoff == None:
            return not self._option("disablemail", email)
        self._option("disablemail", email, not onoff)

    def subscribe(self, email, full_name=None):
        if full_name:
            email = f"{full_name} <{email}>"
        return self.mass_subscribe([email])

    def mass_subscribe(self, emails):
        url2 = f"{self.service.adminurl }/admin/{self.mailinglist}/members/add"
        params = {
            "send_welcome_msg_to_this_batch": "0",
            "send_notifications_to_list_owner": LIST_OWNER_NOTIFS,
            "subscribees": "\n".join(emails),
            "invitation": "",
            "setmemberopts_btn": "Submit Your Changes",
        }
        return self._adminform(url2, params)

    def unsubscribe(self, email):
        url2 = f"{ self.service.adminurl }/admin/{self.mailinglist}/members/remove"
        params = {
            "send_unsub_ack_to_this_batch": "0",
            "send_unsub_notifications_to_list_owner": LIST_OWNER_NOTIFS,
            "unsubscribees": email,
            "setmemberopts_btn": "Submit Your Changes",
        }
        return self._adminform(url2, params)

    def roster(self):
        url2 = f"{self.service.adminurl}/admin/{self.mailinglist}/members"
        body = self.service.post(self.mailinglist, url2, {})
        tree = html.fromstring(body)

        # Check if we get all emails - or if we need to paginate.
        m1 = re.search(
            "<center><em>(\d+) members total, (\d+) shown</em></center>", str(body)
        )
        m2 = re.search("<center><em>(\d+) members total</em></center>", str(body))
        if m1:
            cnt = m1.group(1)
        elif m2:
            cnt = m2.group(1)
        else:
            raise MailmanException(f"Could not retrieve roster.")

        letters = []
        for url in tree.xpath("//a/@href"):
            m = re.search("\?letter=(.)$", url)
            if m:
                letters.append(m.group(1))
        vals = []

        vals.extend(tree.xpath('//input[@name="user" and @type="HIDDEN"]/@value'))

        for l in letters[1:]:
            url3 = f"{url2}?letter={l}"
            body = self.service.post(self.mailinglist, url3, {})
            tree = html.fromstring(body)
            vals.extend(tree.xpath('//input[@name="user" and @type="HIDDEN"]/@value'))

        if int(cnt) != len(vals):
            raise MailmanException(f"Could not retrieve complete roster.")

        # return [email.replace('--at--', '@') for email in vals]
        return [urllib.parse.unquote(email) for email in vals]

    def is_subscribed(self):
        try:
            d = self.delivery
            return True
        except MailmanAccessNoSuchSubscriber:
            pass
        return False

    def _option(self, field, email, onoff=None):
        params = {
            "options-submit": "Submit My Changes",  # essential magic - gleaned from the ./Mailman/Cgi/options.py
        }
        if onoff != None:
            if onoff:
                onoff = "1"
            else:
                onoff = "0"
            logger.info(f"Setting {email}@{self.mailinglist} {field} = {onoff}")
        else:
            logger.info(f"Reading {email} {field}")

        params[field] = onoff

        email = re.sub("@", "--at--", email)
        url2 = f"{ self.service.adminurl }/options/{self.mailinglist}/{email}"
        return self._adminform(url2, params)

    def _adminform(self, url2, params):
        # We prlly should intercepts CSRF at a handler
        # level - and hide it from subsequent calls. I.e.
        # make a CSRF OpenerDirector.
        #
        try:
            formparams = {}
            get = None
            for k, v in params.items():
                if v == None:
                    get = k
                else:
                    formparams[k] = v

            logger.info(f"Posting with {formparams}")
            body = self.service.post(self.mailinglist, url2, formparams)
            tree = html.fromstring(body)

            # bit of a hack - should be a chat/expect per form type. But these
            # are unique enough for the few functons that we have.
            if "Already a member" in str(body):
                logger.info("Return ok on already a member")
                return True
                raise MailmanAlreadySubscribed("already a member")

            if "Successfully subscribed:" in str(body):
                logger.info("Return ok on sub-sub")
                return True

            if "Successfully Unsubscribed:" in str(body):
                logger.info("Return ok on sub-unsub")
                return True

            if "Cannot unsubscribe non-members:" in str(body):
                raise MailmanAccessNoSuchSubscriber("not found")

            if "List Administrator Password:" in str(body):
                raise MailmanAccessDeniedException("during form post")

            # if 'mailing list membership configuration for' not in str(body) and ' zijn met succes ' not in str(body):
            # raise MailmanAccessNoSuchSubscriber("not found")

            if get:
                val = tree.xpath('//input[@name="' + get + '" and @checked]/@value')[0]
                if str(val) == "0":
                    return False
                if str(val) == "1":
                    return True
                raise MailmanException(f"Could not retrieve {field} settings.")

            results = {}
            for k, v in params.items():
                val = tree.xpath('//input[@name="' + k + '" and @checked]/@value')
                if val and val[0]:
                    results[k] = str(val)

            del formparams["csrf_token"]
            logger.info(f"{url2} {formparams} {results}")
            return results

        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise MailmanAccessDeniedException(f"Access denied")
            raise e

        raise MailmanException(f"Failed to set {field}.")


import sys

if __name__ == "__main__":
    (what, adminurl, mlist, email, password) = sys.argv[1:]
    try:
        service = MailmanService(password, adminurl)
        account = MailmanAccount(service, mlist)
        if what == "info":
            print(f"Delivery: { account.delivery(email) }")
            print(f"Digest:   { account.digest(email) }")
        elif what == "nomail":
            print(account.delivery(email, False))
        elif what == "mail":
            print(account.delivery(email, True))
        elif what == "digest":
            print(account.digest(email, True))
        elif what == "nodigest":
            print(account.digest(email, False))
        elif what == "sub":
            print(account.subscribe(email))
        elif what == "unsub":
            print(account.unsubscribe(email))
        elif what == "roster":
            print("\n".join(account.roster()))
        else:
            print("Eh - just now info, mail, nomail, digest, nodigest, sub and ubsub")
    except MailmanAccessDeniedException as e:
        print("Access denied")
    except MailmanAccessNoSuchSubscriber:
        print("That emailis not on this list.")
