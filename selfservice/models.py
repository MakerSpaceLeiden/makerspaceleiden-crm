from django.db import models
from simple_history.models import HistoricalRecords


class WiFiNetwork(models.Model):
    network = models.CharField(max_length=30)
    password = models.CharField(max_length=30)
    adminsonly = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return self.network

    class Meta:
        ordering = ['network']