from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

import sys, os
import datetime


class Command(BaseCommand):
    help = "Show all danglers"

    def handle(self, *args, **options):
        rc = 0
        none = User.objects.get(id=settings.NONE_ID)
        print("Using <{}> ({}) as the catch all user".format(none, settings.NONE_ID))

        for b in PettycashBalanceCache.objects.all().filter(Q(owner=None)):
            b.message = "Deleted for 'Former Participant' cache entry"
            b.delete()

        for tx in PettycashTransaction.objects.all().filter(Q(dst=None) | Q(src=None)):
            print(
                "%s,%s,%s,%s,%s" % (tx.src, tx.dst, tx.date, tx.description, tx.amount)
            )
            if tx.src == None:
                tx.src = none
            if tx.dst == None:
                tx.dst = none
            tx.message = "Replaced None by the 'Former Participant' catchall"
            tx.save(bypass=True)

        sys.exit(rc)
