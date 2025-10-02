import logging
from datetime import timedelta,datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from moneyed import EUR, Money

from makerspaceleiden.mail import emailPlain, emails_for_group
from members.models import User
from terminal.decorators import is_paired_terminal
from terminal.models import Terminal
from .models import Checkout

from pettycash.views import alertOwnersToChange

from django.contrib.sites.models import Site
x = Site.objects.all()[0]
if x.domain != 'weser.webweaving.org':
    x.domain = 'weser.webweaving.org'
    x.name = 'My Special Site Name'
    x.save()

member = User.objects.all().first()
terminal = Terminal.objects.all().first()
if terminal == None:
   terminal = Terminal(name = "Sumup test", fingerprint = "test", nonce = "foo", date = datetime.now(), accepted = True)
   terminal.save()

amount = Money(10.00, EUR)

try:
    print(f"Payment by {member} on terminal {terminal} of {amount} send to sumup Solo")
    checkout = Checkout(member=member, amount=amount, terminal = terminal)
    checkout.transact()
    print("Done!")

except Exception as e:
    print(f"Submit failed\n\t{e}")

