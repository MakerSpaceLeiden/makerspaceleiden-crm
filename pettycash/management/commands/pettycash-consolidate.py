from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

import sys, os
from datetime import datetime, timedelta

from moneyed import Money, EUR


class Command(BaseCommand):
    help = "Consolidate account to last N days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dryrun",
            help="Do a dry-run; do not actually save.",
        )
        parser.add_argument("days", nargs=1, type=int)

    def handle(self, *args, **options):
        rc = 0
        days = options["days"][0]

        cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=days)

        torollup = PettycashTransaction.objects.all().filter(date__lt=cutoff_date)

        for user in User.objects.all():
            records = torollup.filter(Q(dst=user) | Q(src=user))

            rollup = PettycashTransaction(
                src=user,
                dst=user,
                date=cutoff_date,
                amount=Money(0, EUR),
                description="Rollup/Consolidation",
            )

            for tx in records:
                print("  -  %s" % tx)
                if tx.dst == user:
                    rollup.amount += tx.amount
                elif tx.src == user:
                    rollup.amount -= tx.amount

            if rollup.amount:
                print(
                    "User %s consolided %d records: %s"
                    % (user, records.count(), rollup.amount)
                )
                if not options["dryrun"]:
                    rollup._change_reason = "Created during manual rollup"
                    rollup.save(bypass=True)
                    print("  -  saved: %s" % rollup)

                print()

        if torollup:
            print("Deleting %d records" % torollup.count())

        if not options["dryrun"]:
            torollup._change_reason = "Purged during manual rollup"
            torollup.delete()

        sys.exit(rc)
