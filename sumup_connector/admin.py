import logging

from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from makerspaceleiden.admin import SimpleHistoryWithDeletedAdmin

