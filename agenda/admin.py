from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Agenda, AgendaChoreStatusChange


@admin.register(Agenda)
class AgendaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "item_title",
        "_startdatetime",
        "_enddatetime",
        "user",
    )
    ordering = ("_startdatetime", "_enddatetime")
    search_fields = ("item_title", "user__username")
    list_filter = ("_startdatetime", "user")
    readonly_fields = ("start_datetime", "end_datetime")


@admin.register(AgendaChoreStatusChange)
class AgendaChoreStatusChangeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "agenda",
        "user",
        "status",
        "created_at",
    )
    ordering = ["created_at"]
    search_fields = ("agenda__name", "user__username")
    list_filter = ("agenda", "user", "status")
