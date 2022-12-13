from lxml import etree
import re
from django.core.management.base import BaseCommand, CommandError
import csv

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
    help = "Extract member payments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dryrun",
            help="Do a dry-run; do not actually save.",
        )
        parser.add_argument(
            "--skip-uid-check",
            action="store_true",
            dest="skipcheck",
            help="Do not check against the databae",
        )
        parser.add_argument("iban2member-tsv", nargs=1, type=str)
        parser.add_argument("camt53-xml-file", nargs=1, type=str)

    def handle(self, *args, **options):
        mappingfile = options["iban2member-tsv"][0]
        file = options["camt53-xml-file"][0]
        verbosity = int(options["verbosity"])
        dryrun = options["dryrun"]
        skipcheck = options["skipcheck"]
        rc = 0
        mapping = {}
        with open(mappingfile,'r') as fd:
              rd = csv.reader(fd, delimiter="\t", quotechar='"')
              l = 0
              for line in rd:
                   l = l + 1
                   if len(line) < 1 or int(line[1]) < 1 or int(line[1])>5000:
                       print("Error in mapping file {} - line {}:{}".format(mappingfile,l,line))
                       sys.exit(1)
                   mapping[ line[0] ] = line[1]

        if verbosity > 2:
            print("Processing %s", file)

        triggerwords = ['bijdrage', 'contributie', 'deelnemerschap', 'maandelijks', 'monthly','contribution','lidmaatschap', 'deelname']
        results = camt53_process(file, triggerwords, mapping, skipcheck)
        paid = []
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

            paid.append(out)
            if verbosity > 2:
                print("User {}: {} marked as paid".format(out['user'].id, out['user']))

        if verbosity > 2:
            print("Done processing %s -- exit code %d" % (file, rc))

        print("\nRecognized payments\n");
        for out in paid:
             if skipcheck:
                  print("{}\t{}\t{}".format(out['uid'], out['date'], out['name_str']))
             else:
                  print("{}\t{}\t{}\n\t{}".format(out['user'].id, out['date'], out['user'], out))
        sys.exit(rc)
