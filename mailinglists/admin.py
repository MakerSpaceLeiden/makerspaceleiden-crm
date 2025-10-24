import logging

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Mailinglist, Subscription

logger = logging.getLogger(__name__)


@admin.register(Mailinglist)
class MailinglistAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


def subscribe_selected(modeladmin, request, queryset):
    for sub in queryset:
        sub.active = True
        sub.save()


subscribe_selected.short_description = "Activate selected"


def unsubscribe_selected(modeladmin, request, queryset):
    for sub in queryset:
        sub.active = False
        sub.save()


unsubscribe_selected.short_description = "Deactivate selected"


@admin.register(Subscription)
class SubscriptionAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("mailinglist", "member", "active", "digest")
    actions = [subscribe_selected, unsubscribe_selected]
