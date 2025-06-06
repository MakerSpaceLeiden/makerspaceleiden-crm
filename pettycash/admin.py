import logging

from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from makerspaceleiden.admin import SimpleHistoryWithDeletedAdmin

from .forms import PettycashSkuForm
from .models import (
    PettycashBalanceCache,
    PettycashImportRecord,
    PettycashReimbursementRequest,
    PettycashSku,
    PettycashStation,
    PettycashTransaction,
)

logger = logging.getLogger(__name__)


class PettycashSkuAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("pk", "name", "amount", "description")
    form = PettycashSkuForm
    pass


# class PettycashTerminalAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
#    list_display = ("accepted", "date", "get_station", "name", "fingerprint")
#    readonly_fields = ["fingerprint", "nonce"]
#
#    def get_station(self, terminal):
#        try:
#            station = PettycashStation.objects.get(terminal=terminal)
#            return station.description
#        except ObjectDoesNotExist:
#            pass
#        return "-"
#
#    get_station.short_description = "Station"
#    get_station.admin_order_field = "station__name"


class PettycashStationAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("description", "location", "terminal")
    formfield_overrides = {
        models.ManyToManyField: {"widget": CheckboxSelectMultiple},
    }

    # if you forget to enable your default in the pricelist; it is auto added.
    #
    def save_related(self, request, form, formsets, change):
        super(PettycashStationAdmin, self).save_related(request, form, formsets, change)
        if form.cleaned_data["default_sku"]:
            form.instance.available_skus.add(form.cleaned_data["default_sku"])


class PettycashTransactionAdmin(ImportExportModelAdmin, SimpleHistoryWithDeletedAdmin):
    list_display = ("date", "dst", "src", "amount", "description")
    search_fields = [
        "description",
        "src__first_name",
        "src__last_name",
        "dst__first_name",
        "dst__last_name",
    ]
    pass


class PettycashBalanceCacheAdmin(ImportExportModelAdmin, SimpleHistoryWithDeletedAdmin):
    list_display = ("owner", "balance", "lasttxdate")
    search_fields = ["owner__first_name", "owner__last_name"]
    pass


class PettycashReimbursementRequestAdmin(
    ImportExportModelAdmin, SimpleHistoryWithDeletedAdmin
):
    search_fields = [
        "description",
        "src__first_name",
        "src__last_name",
        "dst__first_name",
        "dst__last_name",
    ]
    list_display = ("date", "amount", "description", "dst")
    pass


class PettycashImportRecordAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("date", "by")
    pass


admin.site.register(PettycashSku, PettycashSkuAdmin)
# admin.site.register(PettycashTerminal, PettycashTerminalAdmin)
admin.site.register(PettycashStation, PettycashStationAdmin)
admin.site.register(PettycashTransaction, PettycashTransactionAdmin)
admin.site.register(PettycashBalanceCache, PettycashBalanceCacheAdmin)
admin.site.register(PettycashReimbursementRequest, PettycashReimbursementRequestAdmin)
admin.site.register(PettycashImportRecord, PettycashImportRecordAdmin)
