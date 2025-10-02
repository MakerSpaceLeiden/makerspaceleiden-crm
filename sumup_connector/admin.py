import logging
import json

from django import forms
from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from django.utils.html import format_html

from makerspaceleiden.admin import SimpleHistoryWithDeletedAdmin

from .models import Checkout

class CheckoutAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
  readonly_fields = ['extra_information','date','member','amount','terminal','client_transaction_id','transaction_id','transaction_date']
  exclude = ['debug_note']

  def extra_information(self, instance):
    val = instance.debug_note
    if isinstance(val,str):
       val = json.loads(val)
    if isinstance(val,dict):
       val = json.dumps(val, sort_keys=True, indent=4)
    return format_html("<pre>{}</pre>",val)

  pass

admin.site.register(Checkout, CheckoutAdmin)
