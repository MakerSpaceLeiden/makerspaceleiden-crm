from lxml import etree
import re
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

from pettycash.camt53 import camt53_process

from moneyed import Money, EUR

import sys, os
import datetime
import pwd


class Command(BaseCommand):
    help = "Import CAM53 file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dryrun",
            help="Do a dry-run; do not actually save.",
        )
        parser.add_argument("camt53-xml-file", nargs=1, type=str)

    def handle(self, *args, **options):
        file = options["camt53-xml-file"][0]
        verbosity = int(options["verbosity"])
        dryrun = options["dryrun"]
        rc = 0

        if verbosity > 2:
            print("Processing %s", file)

        results = camt53_process(file)

        for out in results:
            if out.get("error", False):
                rc = rc + 1

            if verbosity > 1 or out.get("error", False):
                print("Txref: %s" % (out.get("ref", "???")))

            if verbosity > 2 or out.get("error", False):
                print(
                    """\
     Rekening:     %s %s
     Amount:       %s
     Omschrijving: %s
"""
                    % (
                        out.get("iban_str", None),
                        out.get("name_str", None),
                        out.get("amount_str", None),
                        out.get("details", None),
                    )
                )

            if not out.get("success", False):
                if verbosity > 2 or out.get("error", False):
                    print(out["msg"])
                    print()
                elif verbosity > 1:
                    print(out["msg"])
                continue

            try:
                tx = PettycashTransaction(
                    src=User.objects.get(id=settings.POT_ID),
                    dst=out["user"],
                    amount=out["amount"],
                )
                tx.description = out["description"]
                tx._change_reason = (
                    "TXREF=%s HOLDER=%s IBAN=%s by script, ran by %s"
                    % (
                        out["ref"],
                        out["name_str"],
                        out["iban_str"],
                        pwd.getpwuid(os.getuid()).pw_name,
                    )
                )
                if not dryrun:
                    tx.save()
                if verbosity < 2:
                    print("Txref: %s" % (out.get("ref", "???")))
                print(out["msg"])
                if verbosity > 1:
                    print()
            except Exception as e:
                print("ERROR - Could not process '%s': %s" % (out["ref"], e))

        if verbosity > 2:
            print("Done processing %s -- exit code %d" % (file, rc))

        sys.exit(rc)
