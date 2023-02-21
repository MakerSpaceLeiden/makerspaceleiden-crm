from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

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
    help = "Sync roster from remote service; and create/sync it with the local one."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help="List all mailing lists; rather than just one",
        )
        parser.add_argument(
            "--dryrun",
            dest="dry",
            action="store_true",
            help="Show what would be done; but do not do it",
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

        parser.add_argument("dir", choices=["list2crm", "crm2list", "compare"])
        parser.add_argument("listname", nargs="*")

    def handle(self, *args, **options):
        if options["all"]:
            lists = Mailinglist.objects.all()
        else:
            lists = [Mailinglist.objects.get(name=name) for name in options["listname"]]

        if len(lists) == 0:
            raise CommandError("Noting to do.")

        # We do not use the default option of parser - as to not reveal settings needlessly.
        password = settings.ML_PASSWORD
        if options["password"]:
            password = options["password"]

        url = settings.ML_ADMINURL
        if options["url"]:
            url = options["url"]

        dryrun = options["dry"]

        pull = False
        push = False
        if options["dir"] == "list2crm":
            pull = True
        elif options["dir"] == "crm2list":
            push = True
        elif not dryrun:
            print("Comparing - automatically a dryrun")
            dryrun = True

        service = MailmanService(password, url)
        for mlist in lists:
            print(f"# {mlist.name}: {mlist.description}")

            # system = []
            # for s in  Subscription.objects.all().filter(mailinglist__name = mlist):
            #    system.append(s.member.email)
            # known = User.objects.all().values_list('email', flat=True)

            users = User.objects.filter(is_active=True)
            known = []
            e2u = {}
            for u in users:
                known.append(u.email)
                e2u[u.email.lower()] = u

            # system = Subscription.objects.all().values_list('member__email', flat=True)
            subs = Subscription.objects.all().filter(mailinglist=mlist)
            system = []
            e2s = {}
            for s in subs:
                system.append(s.member.email)
                e2s[s.member.email.lower()] = s

            account = MailmanAccount(service, mlist)
            roster = account.roster()

            for email in sorted(list(set(roster) | set(system) | set(known))):
                if email in roster and email in system:
                    sub = e2s[email.lower()]

                    print(f"{email}\n\tboth on roster and on server.")

                    v = account.delivery(email)
                    if sub.active != v:
                        if pull:
                            print(f"\tACTION: active flag to {v} - list is leading")
                            if not dryrun:
                                sub.active = v
                                sub.save()
                        if push:
                            print(
                                f"\tACTION: active flag to {sub.active} - crm is leading"
                            )
                            if not dryrun:
                                account.delivery(email, sub.active)
                    else:
                        print(f"\tactive/delivery flag in sync.")

                    v = account.digest(email)
                    if sub.digest != v:
                        if pull:
                            print(f"\tACTION: digest flag to {v} - list is leading")
                            if not dryrun:
                                sub.digest = v
                                sub.save()
                        if push:
                            print(
                                f"\tACTION: digest flag to {sub.digest } - crm is leading"
                            )
                            # if not dryrun:
                            #   acount.digest(email, sub.digest)
                    else:
                        print(f"\tdigest flag in sync.")

                elif email in known and email in system:
                    print(
                        f"{email}\n \tmissing on roster - but we think it should be subscribed"
                    )
                    if pull:
                        print(f"\tDEFER: nothing - as we're pulling from the list")

                    if push:
                        print(f"\tACTION: Subscribing on list -- crm is leading")
                        if not dryrun:
                            sub = e2s[email.lower()]
                            sub.subscribe()
                            # sub.changeReason("Sync Subscribed during command sync")
                            sub.save()

                elif email in known and email in roster:
                    print(
                        f"{email}\n \ton the roster - but not recorded as subscribed."
                    )
                    if pull:
                        print(
                            f"\tACTION: record as subscribed wth active delivery -- list is leading"
                        )
                        if not dryrun:
                            s = Subscription(
                                member=e2u[email],
                                mailinglist=mlist,
                                digest=False,
                                active=True,
                            )
                            s.save()
                    if push:
                        print(f"\tDEFER: nothing - as the crm is leading")

                elif email in known:
                    print(
                        f"{email}\n \tmissing on roster - and not recorded as subscribed."
                    )
                    if pull:
                        print(f"\tDEFER: not doing anything - list is leading'")
                    if push:
                        print(
                            f"\tACTION: Subscribing onto the roster AND recoring as subscribed with delivery off"
                        )
                        if not dryrun:
                            s = Subscription(
                                member=e2u[email],
                                mailinglist=mlist,
                                digest=False,
                                active=False,
                            )
                            s.subscribe()
                            s.save()

                elif email in roster:
                    print(f"{email}\n \tnot in the crm, but on the roster")
                    if pull or push:
                        print(f"\tDEFER: modify/add user in crm or delete from roster")
                else:
                    raise Exception("bug")

        sys.exit(0)
