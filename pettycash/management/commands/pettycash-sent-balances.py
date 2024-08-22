import sys
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from moneyed import EUR, Money

from makerspaceleiden.mail import emailPlain
from pettycash.models import (
    PettycashBalanceCache,
    PettycashImportRecord,
    PettycashSku,
    PettycashTransaction,
)


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
    help = "Sent balance overview of everyone"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to",
            type=str,
            help="Sent the message to a different addres (default is to %s)"
            % (settings.MAILINGLIST),
        )

        parser.add_argument(
            "--direct",
            dest="direct",
            action="store_true",
            help="Sent the message directly to the users, rather than to the mailing list.",
        )

        parser.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help="Also include people with a 0 balance.",
        )

        parser.add_argument(
            "--days",
            dest="days",
            action="store",
            default=100,
            type=int,
            help="Ignore people who did not do a transaction in this many days (default is 100)",
        )

        parser.add_argument(
            "--save",
            dest="save",
            type=str,
            help="Save the message as rfc822 blobs rather than sending. Useful as we sort out dkim on the server. Pass the output directory as an argument",
        )

        parser.add_argument(
            "--dry-run",
            dest="dryrun",
            action="store_true",
            help="Do a dry run; do not actually sent",
        )

    def handle(self, *args, **options):
        _ = int(options["verbosity"])
        cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=options["days"])
        rc = 0

        if options["save"]:
            settings.EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
            settings.EMAIL_FILE_PATH = options["save"]

        balances = PettycashBalanceCache.objects.order_by("balance")
        if not options["all"]:
            balances = balances.filter(
                (
                    Q(balance__gt=Money(0, EUR))
                    # & Q(last__date__gt=cutoff_date)
                )
                | Q(balance__lt=Money(0, EUR))
            ).filter(~Q(owner=settings.POT_ID) & ~Q(owner=settings.NONE_ID))

        skus = PettycashSku.objects.order_by("name")
        per_sku = []
        for sku in skus:
            e = {
                "name": sku.name,
                "sku": sku,
                "description": sku.description,
                "amount": Money(0, EUR),
                "count": 0,
                "price": sku.amount,
            }
            desc = sku.name
            if sku.description:
                desc = sku.description
            for tx in PettycashTransaction.objects.all().filter(
                description__startswith=desc
            ):
                e["amount"] += tx.amount
                e["count"] += 1
            per_sku.append(e)

        dest = settings.MAILINGLIST
        if options["to"]:
            dest = options["to"]

        if options["direct"]:
            dest = balances.values_list("owner__email", flat=True)

        if balances.count():
            sendEmail(balances, skus, per_sku, dest, forreal=(not options["dryrun"]))
        else:
            print("No balances sent - none done since %s" % cutoff_date)

        sys.exit(rc)
