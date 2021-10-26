from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Servicelog


class ServicelogAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


admin.site.register(Servicelog, ServicelogAdmin)
