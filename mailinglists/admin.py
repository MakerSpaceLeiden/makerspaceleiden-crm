from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Mailinglist, Subscription

class MailinglistAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass

admin.site.register(Mailinglist, MailinglistAdmin)

class SubscriptionAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
     pass
admin.site.register(Subscription, SubscriptionAdmin)



