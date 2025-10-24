import logging

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import PettycreditClaim, PettycreditClaimChange

logger = logging.getLogger(__name__)


@admin.register(PettycreditClaim)
class PettycreditClaimAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass


@admin.register(PettycreditClaimChange)
class PettycreditClaimChangeAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass
