from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Memberbox


@admin.register(Memberbox)
class MemberboxAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    search_fields = [
        "location",
        "owner__first_name",
        "owner__last_name",
        "owner__email",
    ]
    list_display = (
        "location",
        "owner",
    )
    pass
