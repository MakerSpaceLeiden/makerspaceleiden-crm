import sys
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from moneyed import EUR, Money

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from makerspaceleiden.mail import emailPlain
from pettycash.models import (
    PettycashBalanceCache,
    PettycashImportRecord,
    PettycashSku,
    PettycashTransaction,
)
from django.template.loader import render_to_string



def sendEmail(
    skus,
    per_sku,
    toinform,
    attachments = [],
    template="usage-sku-overview-email.txt",
    forreal=True,
):
    for e in [toinform] if isinstance(toinform, str) else toinform:
        emailPlain(
            template,
            toinform=[e],
            context={
                "per_sku": per_sku,
                "skus": skus,
                "date": datetime.now(tz=timezone.utc),
                "base": settings.BASE,
            },
            forreal=forreal,
            attachments = attachments,
        )


class Command(BaseCommand):
    help = "Sent SKU usage"

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
        rc = 0

        if options["save"]:
            settings.EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
            settings.EMAIL_FILE_PATH = options["save"]

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

        csv = render_to_string('usage-sku.csv',
            context={
                "per_sku": per_sku,
                "skus": skus,
                "base": settings.BASE,
            })

        attachment = MIMEApplication(csv, name = 'usage-sku.csv')
        attachment.add_header("Content-Disposition", 'inline; filename="usage-sku.csv"')

        sendEmail(skus, per_sku, dest, [ attachment ], forreal=(not options["dryrun"]))

        sys.exit(rc)
