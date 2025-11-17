from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Storage


@admin.register(Storage)
class StorageAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass
