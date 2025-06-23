from django.contrib import admin

from .models import Agenda


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = (
        "item_title",
        "startdate",
        "starttime",
        "enddate",
        "endtime",
        "user",
    )
    ordering = ("startdate", "starttime")
    search_fields = ("item_title", "user__username")
    list_filter = ("startdate", "user")
