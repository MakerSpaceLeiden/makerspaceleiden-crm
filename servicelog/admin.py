from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Servicelog


@admin.register(Servicelog)
class ServicelogAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass
