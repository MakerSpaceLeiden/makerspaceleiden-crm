from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import WiFiNetwork


class WiFiNetworkAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


admin.site.register(WiFiNetwork, WiFiNetworkAdmin)
