import argparse
import sys

from django.core.management.base import BaseCommand
from moneyed import EUR, Money

from pettycash.models import PettycashSku


class Command(BaseCommand):
    help = "Import CSV pricelist of amount, name, description"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dryrun",
            help="Do a dry-run; do not actually save.",
        )
        parser.add_argument("pricelist-csv-file", nargs=1, type=argparse.FileType("r"))

    def handle(self, *args, **options):
        file = options["pricelist-csv-file"][0]
        verbosity = int(options["verbosity"])
        rc = 0

        for file in options["pricelist-csv-file"]:
            if verbosity > 1:
                print("Processing %s" % (file.name))
            lno = 0
            for line in file:
                if verbosity > 2:
                    print(line)
                lno = lno + 1
                line.strip()
                try:
                    amount, name, description = line.split(",", 3)
                    amount = Money(amount, EUR)
                except Exception as e:
                    print(
                        "Could not read line %d@%s\n\t%s\n\t%s\n" % (lno, file, line, e)
                    )
                    sys.exit(1)

                sku, wasCreated = PettycashSku.objects.get_or_create(name=name)

                sku.name = name
                sku.amount = amount
                sku.descrioption = description

                if wasCreated:
                    sku.changeReason = (
                        "Added during bulk import from file %s" % file.name
                    )
                else:
                    sku.changeReason = (
                        "Updated during bulk import from file %s" % file.name
                    )

                if not options["dryrun"]:
                    sku.save()

                if verbosity > 0:
                    print(sku)

        if verbosity > 2:
            print("Done processing %s -- exit code %d" % (file.name, rc))

        sys.exit(rc)
