from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Chore


class ChoreAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = (
        'name',
        'description',
        'class_type',
        'configuration',
        'creator',
        'created_at',
    )


admin.site.register(Chore, ChoreAdmin)
