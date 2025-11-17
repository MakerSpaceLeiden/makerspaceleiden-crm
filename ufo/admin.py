from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Ufo


@admin.register(Ufo)
class UfoAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass
