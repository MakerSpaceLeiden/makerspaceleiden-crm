import sys

from django.core.management.base import BaseCommand

from acl.models import Machine, useNeedsToStateStr
from members.models import User


class Command(BaseCommand):
    help = "Export binary tag/member file for a given machine."

    def add_arguments(self, parser):
        parser.add_argument("machine", type=str, help="Machine this list is for")
        parser.add_argument("user", type=str, help="User that list is for")

    def handle(self, *args, **options):
        rc = 0

        machine = options["machine"]
        user = options["user"]

        machine = Machine.objects.get(node_machine_name=machine)
        user = User.objects.get(last_name=user)

        (needs, has) = machine.useState(user)
        res = needs & has
        print(f"has({has:X}) & needs({needs:X}) = {res:X}")
        print(useNeedsToStateStr(needs, has))

        sys.exit(rc)
