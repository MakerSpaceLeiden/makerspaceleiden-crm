from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin

from .models import Mainssensor


class MainssensorAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = Mainssensor


admin.site.register(Mainssensor, MainssensorAdmin)
