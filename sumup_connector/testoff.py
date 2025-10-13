"""

1)	Relies on
                ssh -R 8000:localhost:8000 fqdn

        or similar to expose local django to internet

2)	Relies on

                <Location /sumup>
                        ProxyPass http://127.0.0.1:8000/sumup
                        Require all granted
                </Location>

        in a webserver on the internet side to map things through
"""

import datetime
import secrets
import time

from django.contrib.sites.models import Site
from moneyed import EUR, Money

from members.models import User
from terminal.models import Terminal

from .models import Checkout

x = Site.objects.all()[0]
if x.domain != "weser.webweaving.org":
    x.domain = "weser.webweaving.org"
    x.name = "My Special Site Name"
    x.save()

member = User.objects.all().first()
terminal = Terminal.objects.all().first()
if terminal is None:
    terminal = Terminal(
        name="Sumup test",
        fingerprint="test",
        nonce="foo",
        date=datetime.now(),
        accepted=True,
    )
    terminal.save()

amount = Money(10.00, EUR)

print(f"Payment by {member} on terminal {terminal} of {amount} send to sumup Solo")

checkout = Checkout(member=member, amount=amount, terminal=terminal)
checkout.transact()
checkout.deposit(
    timestamp=datetime.datetime.now(), transaction_id=secrets.token_urlsafe(16)
)
time.sleep(60)

checkout.deposit()
checkout = Checkout(member=member, amount=amount, terminal=terminal)
checkout.transact()
checkout.deposit(
    timestamp=datetime.datetime.now(), transaction_id=secrets.token_urlsafe(16)
)
time.sleep(60)

checkout = Checkout(member=member, amount=amount, terminal=terminal)
checkout.transact()
