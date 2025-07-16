from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Agenda


@admin.register(Agenda)
class AgendaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "item_title",
        "startdate",
        "starttime",
        "enddate",
        "endtime",
        "start_datetime",
        "end_datetime",
        "user",
    )
    ordering = ("startdate", "starttime")
    search_fields = ("item_title", "user__username")
    list_filter = ("startdate", "user")
    readonly_fields = ("start_datetime", "end_datetime")
