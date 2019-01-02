from django.core.management.base import BaseCommand, CommandError

from simple_history.models import HistoricalRecords
from members.models import User
from members.models import Tag,User
from selfservice.models import WiFiNetwork

import sys,os
''' 
Expert a file like

# wifi network, password
Makerspace-5ghz,SecretPassword
'''

class Command(BaseCommand):
    help = 'Import CSV file with SSID/Password pairs for the wifi'

    def handle(self, *args, **options):

        for line in sys.stdin:
           line = line.strip()
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
