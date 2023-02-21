from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

from members.models import User
from mailinglists.models import (
    Mailinglist,
    Subscription,
    MailmanAccount,
    MailmanService,
)

import sys, os


class Command(BaseCommand):
    help = "Compare mailinglist(s) in mailman with database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help="List all mailing lists; rather than just one",
        )
        parser.add_argument(
            "--url",
            dest="url",
            type=str,
            help="Admin URL",
        )
        parser.add_argument(
            "--password",
            dest="password",
            type=str,
            help="Admin Password",
        )
        parser.add_argument(
            "--systemonly",
            dest="systemonly",
            action="store_true",
            help="Just show system data; do not query mailinglist service",
        )

        parser.add_argument("listname", nargs="*")

    def handle(self, *args, **options):
        if options["all"]:
            lists = Mailinglist.objects.all().order_by("name")
        else:
            lists = [Mailinglist.objects.get(name=name) for name in options["listname"]]

        if len(lists) == 0:
            raise CommandError("Noting to do.")

        password = settings.ML_PASSWORD
        if options["password"]:
            password = options["password"]

        url = settings.ML_ADMINURL
        if options["url"]:
            url = options["url"]

        service = MailmanService(password, url)
        for mlist in lists:
            print(f"# {mlist.name}: {mlist.description} Mandatory: {mlist.mandatory}")

            dr = "."
            if options["systemonly"]:
                dr = "?"
                roster = []
            else:
                account = MailmanAccount(service, mlist)
                roster = account.roster()

            system = []
            for s in Subscription.objects.all().filter(mailinglist__name=mlist):
                system.append(s.member.email.lower())

            for email in sorted(list(set(roster) | set(system))):
                r = dr
                email.lower()
                if email in roster:
                    r = "R"
                s = "."
                if email in system:
                    s = "S"
                print(f"{r} {s} {mlist} {email}")

        sys.exit(0)
