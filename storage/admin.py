from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Storage


class StorageAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


admin.site.register(Storage, StorageAdmin)
