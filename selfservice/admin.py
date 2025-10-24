from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import WiFiNetwork


@admin.register(WiFiNetwork)
class WiFiNetworkAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass
