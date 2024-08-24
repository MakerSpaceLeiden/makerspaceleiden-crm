from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Chore, ChoreVolunteer


class ChoreAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = (
        "name",
        "description",
        "class_type",
        "configuration",
        "creator",
        "created_at",
        "wiki_url",
    )


class ChoreVolunteerAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = (
        "user",
        "chore",
        "timestamp",
        "created_at",
    )


admin.site.register(Chore, ChoreAdmin)
admin.site.register(ChoreVolunteer, ChoreVolunteerAdmin)
