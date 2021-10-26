from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Ufo


class UfoAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


admin.site.register(Ufo, UfoAdmin)
