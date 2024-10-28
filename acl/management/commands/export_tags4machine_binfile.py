import sys

from django.core.management.base import BaseCommand

from acl.views import tags4machineBIN


class Command(BaseCommand):
    help = "Export binary tag/member file for a given machine."

    def add_arguments(self, parser):
        parser.add_argument("machine", type=str, help="Machine this list is for")

    def handle(self, *args, **options):
        rc = 0

        terminal = None
        machine = options["machine"]

        sys.stdout.buffer.write(tags4machineBIN(terminal, machine))

        sys.exit(rc)
