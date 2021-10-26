from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin

from .models import Unknowntag


class UnknownagAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = Unknowntag


admin.site.register(Unknowntag, UnknownagAdmin)
