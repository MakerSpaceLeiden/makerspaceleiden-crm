import calendar
import logging
from datetime import date

from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionMixin, ImportExportModelAdmin
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


@admin.register(PettycashSku)
class PettycashSkuAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("pk", "name", "amount", "description")
    form = PettycashSkuForm
    pass


#            pass
#


@admin.register(PettycashStation)
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


class MonthFilter(admin.SimpleListFilter):
    title = _("month")
    parameter_name = "month"

    def lookups(self, request, model_admin):
        # Generate last 12 months including current month
        today = date.today()
        months = []

        for i in range(12):
            # Calculate the year and month i months ago
            month = today.month - i
            year = today.year

            # Handle year rollover when month becomes <= 0
            while month <= 0:
                month += 12
                year -= 1

            month_name = calendar.month_name[month]
            display = f"{month_name} {year}"
            value = f"{year}-{month:02d}"
            months.append((value, display))

        return months

    def queryset(self, request, queryset):
        # Filter queryset by selected month
        val = self.value()
        if val:
            try:
                year, month = map(int, val.split("-"))
                return queryset.filter(date__year=year, date__month=month)
            except ValueError:
                # If the value is malformed, just return unfiltered queryset
                return queryset

        return queryset


@admin.register(PettycashTransaction)
class PettycashTransactionAdmin(
    ImportExportModelAdmin, SimpleHistoryWithDeletedAdmin, ExportActionMixin
):
    list_display = ("date", "dst", "src", "amount", "description")
    search_fields = [
        "description",
        "src__first_name",
        "src__last_name",
        "dst__first_name",
        "dst__last_name",
    ]
    list_filter = (MonthFilter,)
    pass


@admin.register(PettycashBalanceCache)
class PettycashBalanceCacheAdmin(ImportExportModelAdmin, SimpleHistoryWithDeletedAdmin):
    list_display = ("owner", "balance", "lasttxdate")
    search_fields = ["owner__first_name", "owner__last_name"]
    pass


@admin.register(PettycashReimbursementRequest)
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


@admin.register(PettycashImportRecord)
class PettycashImportRecordAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("date", "by")
    pass
