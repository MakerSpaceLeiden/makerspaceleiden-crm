import argparse

from django.core.management.base import BaseCommand

from selfservice.models import WiFiNetwork


class Command(BaseCommand):
    """
    Imports SSID-password pairs for the network according to the following table format:

    | SSID            | PSK          | staff only |
    | MakerSpace-5GHz | SomePassword | 0 or 1     |
    """

    help = "Import CSV file with SSID/Password pairs for the wifi"

    def add_arguments(self, parser):
        parser.add_argument("inputfile", nargs=1, type=argparse.FileType("r"))

    def handle(self, *args, **options):
        for file in options["inputfile"]:
            for line in file:
                line.strip()
                print(line)
                network, password, staffOnly = line.split(",")
                if int(staffOnly) > 0:
                    staffOnly = True
                else:
                    staffOnly = False

                if network == "name" or network.startswith("#"):
                    continue

                wifi, wasCreated = WiFiNetwork.objects.get_or_create(network=network)
                wifi.network = network
                wifi.password = password
                wifi.adminsonly = staffOnly

                if wasCreated:
                    wifi.changeReason = "Added during bulk import."
                else:
                    wifi.changeReason = "Updated during bulk import."
                wifi.save()
