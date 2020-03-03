from django.core.management.base import BaseCommand, CommandError

from simple_history.models import HistoricalRecords
from members.models import User
from members.models import Tag,User
from selfservice.models import WiFiNetwork

#import sys,os
import argparse
''' 
Imports SSID-password pairs for the network according to the following table format:

| SSID            | PSK          |
| MakerSpace-5GHz | SomePassword |
'''

class Command(BaseCommand):
    help = 'Import CSV file with SSID/Password pairs for the wifi'

    def add_arguments(self, parser):
        parser.add_argument('inputfile', nargs=1, type=argparse.FileType('r'))

    def handle(self, *args, **options):
        for file in options['inputfile']:
            for line in file:
                line.strip()
                print(line)
                network, password= line.split(',')

                if network=='name' or network.startswith('#'):
                    continue

                wifi,wasCreated = WiFiNetwork.objects.get_or_create(network=network)
                wifi.network = network
                wifi.password = password

                if wasCreated:
                    wifi.changeReason = "Added during bulk import."
                else:
                    wifi.changeReason = "Updated during bulk import."
                wifi.save()
