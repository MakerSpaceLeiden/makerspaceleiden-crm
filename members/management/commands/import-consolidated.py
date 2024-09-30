import argparse
import logging

from django.core.management.base import BaseCommand

from acl.models import Entitlement, Machine, PermitType
from memberbox.models import Memberbox
from members.models import Tag, User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Imports user data from file in CSV-format"

    def add_arguments(self, parser):
        parser.add_argument("inputfile", nargs=1, type=argparse.FileType("r"))

    def handle(self, *args, **options):
        """Do your work here"""
        # self.stdout.write('There are {} things!'.format(User.objects.count()))
        user0 = None
        admin = None
        cup = 0

        try:
            admin = User.objects.get(email="admin@admin.nl")
        except Exception:
            raise Exception("No admin; did you run user-init ?")

        woodpermit, wasCreated = PermitType.objects.get_or_create(
            name="Wood Instruction"
        )
        woodpermit.description = "Can issue wood machine entitlement"
        woodpermit.save()

        trustee = None
        for file in options["inputfile"]:
            while True:  # OH GOD
                email = file.readline().strip()
                if email == "":
                    break
                tags = file.readline().strip()
                name = file.readline().strip()
                what = file.readline().strip()
                phone = file.readline().strip()
                member = None

                member, wasCreated = User.objects.get_or_create(email=email)

                member.email = email
                member.set_password("1234")
                if len(phone) > 4:
                    member.phone_number = phone
                if " " in name:
                    member.first_name = name.split(" ", 1)[0]
                    member.last_name = name.split(" ", 1)[1]
                else:
                    member.first_name = name
                    member.last_name = ""
                if len(what.split(" ")) > 1:
                    member.form_on_file = True
                if trustee is None:
                    member.is_staff = True
                    trustee = member
                member.save()
                print("Member={}".format(member))

                for tag in tags.split():
                    Tag.objects.get_or_create(owner=member, tag=tag)
                    print("	tag: {}".format(tag))

                if not user0:
                    user0 = member
                    entit = Entitlement(
                        permit=woodpermit, holder=user0, issuer=admin, active=True
                    )
                    print(user0.email)
                    print(admin.email)
                    print(woodpermit)
                    print(entit)
                    entit.save(bypass_user=admin)

                self.stdout.write("Imported {} <{}>".format(name, email))

                for w in what.split(" "):
                    # loc = Location(name = 'At the usual spot')
                    permit = None
                    permit, wasCreated = PermitType.objects.get_or_create(name=w)
                    permit.description = "The " + w + " permit"
                    permit.permit = woodpermit
                    permit.save()

                    machine, wasCreated = Machine.objects.get_or_create(name=w)
                    machine.description = "The " + w + " machine"
                    # machine.location = lo
                    machine.node_name = "Node" + machine.name.upper()
                    machine.node_machine_name = machine.name.lower()
                    machine.requires_form = True
                    machine.requires_instruction = True
                    machine.requires_permit = permit
                    self.stdout.write("Machine imported {}".format(w))
                    # loc.save()
                    machine.save()

                    #               try:
                    #                 entit,wasCreated = Entitlement.objects.get_or_create(permit = permit, holder = member, issuer = user0)
                    #               except Entitlement.DoesNotExist
                    #               except DoesNotExist:
                    entit = Entitlement()
                    entit.permit = permit
                    entit.holder = member
                    entit.issuer = user0
                    entit.active = True
                    entit.save(bypass_user=admin)
                #               except Exception as e:
                #                 raise e

                col = cup % 6
                row = int(cup / 6) % 6
                k = int(cup / 36)
                cup += 1
                l = "random spot " + str(cup)
                if k == 0:
                    l = "L" + str(col) + str(row)
                if k == 1:
                    l = "R" + str(col) + str(row)

                box, wasCreated = Memberbox.objects.get_or_create(
                    location=l, owner=member
                )
                box.description = "The nice box of " + str(member)
                box.save()
