import sys
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from pettycash.models import PettycashPendingClaim


class Command(BaseCommand):
    help = "Purge claims that are settled (default is older than {} days".format(
        settings.DEFAULT_SETTLED_PURGE_DAYS
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            dest="days",
            action="store",
            default=0,
            type=int,
            help="Purger after this many deays (default is {})".format(
                settings.DEFAULT_SETTLED_PURGE_DAYS
            ),
        )

        parser.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help="Ignore the date; purge verythiung that is settled.",
        )

        parser.add_argument(
            "--dry-run",
            dest="dryrun",
            action="store_true",
            help="Do a dry run; do not actually sent",
        )

    def handle(self, *args, **options):
        rc = 0
        _ = int(options["verbosity"])

        cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=options["days"])

        claims = PettycashPendingClaim.objects.order_by("submitted_date").filter(
            Q(settled=True)
        )
        if not options["all"]:
            claims = claims.filter(
                Q(last_settle_date__date__lt=cutoff_date)
                | (Q(last_settle_date=None) & Q(last_update__date__lt=cutoff_date))
            )
            if _:
                print("Cutoff date: {}".format(cutoff_date))

        for claim in claims:
            if _:
                print("{}".format(claim))
            claim.delete()

        sys.exit(rc)
