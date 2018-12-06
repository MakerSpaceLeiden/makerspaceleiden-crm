from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from import_export.admin import ImportExportModelAdmin

from .models import Machine
from .models import Location
from .models import Instruction

class MachineAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('name','description','location','requires_instruction','requires_form','requires_permit')
admin.site.register(Machine,MachineAdmin)

class LocationAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('name','description')
admin.site.register(Location,LocationAdmin)

class InstructionAdmin(ImportExportModelAdmin):
    pass
admin.site.register(Instruction, InstructionAdmin)

