from django.contrib import admin

from .models import Motd


@admin.register(Motd)
class MotdAdmin(admin.ModelAdmin):
    list_display = ("motd", "startdate", "starttime", "enddate", "endtime", "user")
    ordering = ("startdate", "starttime")
    search_fields = ("motd", "user__username")
    list_filter = ("startdate", "user")
