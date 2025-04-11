import sys
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from makerspaceleiden.mail import emailPlain
from pettycash.models import PettycashImportRecord, PettycashPendingClaim


def sendEmail(
    balances,
    skus,
    per_sku,
    toinform,
    template="balance-overview-email.txt",
    forreal=True,
):
    for e in [toinform] if isinstance(toinform, str) else toinform:
        emailPlain(
            template,
            toinform=[e],
            context={
                "balances": balances,
                "per_sku": per_sku,
                "skus": skus,
                "date": datetime.now(tz=timezone.utc),
                "base": settings.BASE,
                "last_import": PettycashImportRecord.objects.all().last(),
            },
            forreal=forreal,
        )


class Command(BaseCommand):
    help = "Settle auto-claims and alert maintainers to non auto settling claims periodically"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to",
            type=str,
            help="Sent the message to a different addres (default is to %s)"
            % (settings.MAILINGLIST),
        )

        parser.add_argument(
            "--offset",
            dest="offset",
            action="store",
            default=0,
            type=int,
            help="Offset the time by this many seconds; positive is in the future; negative is in the past",
        )

        parser.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help="Ignore the date; do all of them",
        )

        parser.add_argument(
            "--dry-run",
            dest="dryrun",
            action="store_true",
            help="Do a dry run; do not actually sent",
        )

    def handle(self, *args, **options):
        _ = int(options["verbosity"])
        cutoff_date = datetime.now(tz=timezone.utc) - timedelta(
            seconds=options["offset"]
        )
        rc = 0

        # dest = settings.MAILINGLIST
        # if options["to"]:
        #   dest = options["to"]

        claims = PettycashPendingClaim.objects.order_by("submitted_date").filter(
            Q(settled=False) & ~Q(last_settle_date=None)
        )
        if not options["all"]:
            claims = claims.filter(Q(last_settle_date__date__lt=cutoff_date))
            if _:
                print("Cutoff date: {}".format(cutoff_date))

        for claim in claims:
            print("Settling claim {}".format(claim))
            if not options["dryrun"]:
                claim.settle("Claim automatically settled (timed out)")

        sys.exit(rc)
