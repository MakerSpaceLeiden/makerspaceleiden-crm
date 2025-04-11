import logging

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import PettycreditClaim, PettycreditClaimChange

logger = logging.getLogger(__name__)


class PettycreditClaimAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


class PettycreditClaimChangeAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


admin.site.register(PettycreditClaim, PettycreditClaimAdmin)
admin.site.register(PettycreditClaimChange, PettycreditClaimChangeAdmin)
