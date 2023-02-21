from django.core.management.base import BaseCommand, CommandError

from simple_history.models import HistoricalRecords
from members.models import User
from members.models import Tag, User
from acl.models import Machine, Location, PermitType, Entitlement
from memberbox.models import Memberbox
from storage.models import Storage

import argparse

""" 
Imports tool/machine information according to the following table format:

| Name       | instruction-req | permit-req | permit-type | description | location  |
| 3D printer | 1               | 0          |             | 3D-Printer  | Frontroom |
"""


class Command(BaseCommand):
    help = "Imports tool/machine data from file in csv format"

    def add_arguments(self, parser):
        parser.add_argument("inputfile", nargs=1, type=argparse.FileType("r"))

    def handle(self, *args, **options):
        for file in options["inputfile"]:
            for line in file:
                lineData = {
                    "Name": None,
                    "instructionsRequired": None,
                    "permitRequired": None,
                    "permit": None,
                    "description": None,
                    "Location": None,
                }

                line = line.strip()
                print(line)

                (
                    lineData["Name"],
                    lineData["instructionsRequired"],
                    lineData["permitRequired"],
                    lineData["permit"],
                    lineData["description"],
                    lineData["Location"],
                ) = line.split(
                    ","
                )  # name, instructionsRequired, permitRequired, permit, desc, location

                if lineData["Name"] == "name" or lineData["Name"].startswith("#"):
                    continue

                tempPermit = None
                tempLocation = None
                machine = None

                if lineData["permit"]:
                    tempPermit, wasCreated = PermitType.objects.get_or_create(
                        name=lineData["permit"]
                    )
                    tempPermit.description = "Permit to use " + lineData["permit"]
                    tempPermit.changeReason = "Added during bulk import."
                    tempPermit.save()
                    print(tempPermit)

                if lineData["Location"]:
                    tempLocation, wasCreated = Location.objects.get_or_create(
                        name=lineData["Location"]
                    )
                    tempLocation.changeReason = "Added during bulk import."
                    tempLocation.save()
                    print(tempLocation)

                print(lineData["permit"])
                print(tempLocation)

                machine, wasCreated = Machine.objects.get_or_create(
                    name=lineData["Name"]
                )
                machine.description = lineData["description"]

                if lineData["Location"]:
                    machine.location = tempLocation

                if lineData["permit"]:
                    machine.requires_form = True
                    machine.requres_permit = lineData["permit"]

                machine.changeReason = "Added during bulk import."
                machine.save()
