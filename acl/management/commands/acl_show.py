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

        try:
            machine = Machine.objects.get(node_machine_name=machine)
        except Exception:
            try:
                machine = Machine.objects.get(name=machine)
            except Exception:
                machine = Machine.objects.filter(name__icontains=machine)

        try:
            user = User.objects.get(last_name=user)
        except Exception:
            user = User.objects.filter(name__icontains=user)

        (needs, has) = machine.useState(user)
        res = needs & has
        print(
            f"User {user} has({has:X}) & needs({needs:X}) = {res:X} for machine {machine}"
        )
        print(useNeedsToStateStr(needs, has))

        sys.exit(rc)
