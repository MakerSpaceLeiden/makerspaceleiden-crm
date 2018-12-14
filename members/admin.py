from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm

from import_export.admin import ImportExportModelAdmin
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin
from django.utils.translation import ugettext_lazy as _


from .models import Tag, PermitType, Entitlement, User

class UserResource(resources.ModelResource):
    class Meta:
       model = User
       fields = ('username', 'first_name', 'last_name', 'email','is_active','date_joined', 'form_on_file','email_confirmed')
       import_id_fields = ['username','first_name', 'last_name', 'email']

class TagResource(resources.ModelResource):
    class Meta:
       model = Tag
       fields = [ 'owner', 'tag' ]
       import_id_fields = [ 'owner', 'tag' ]

class EntitlementResource(resources.ModelResource):
    class Meta:
       model = Entitlement
       fields = [ 'permit', 'holder', 'issuer' ]
       import_id_fields = [ 'permit', 'holder', 'issuer' ]
       # import_id_fields = [ 'permit', 'holder', 'issuer' ]

# Define a new User admin
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin, SimpleHistoryAdmin):
    resource_class = UserResource
    fieldsets = (
        (None,                 {'fields': ('email', 'password')}),
        (_('Membership'),      {'fields': ('first_name', 'last_name', 'form_on_file', 'email_confirmed')}),
        (_('Permissions'),     {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

admin.site.register(User,UserAdmin)

class TagAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    resource_class = TagResource

admin.site.register(Tag,TagAdmin)

# class PermitAdmin(ImportExportModelAdmin,admin.ModelAdmin):
class PermitAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    list_display = ('name','description')
admin.site.register(PermitType,PermitAdmin)

# class EntitlementAdmin(ImportExportModelAdmin,admin.ModelAdmin, SimpleHistoryAdmin):
class EntitlementAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    list_display = ('permit','holder','issuer')
    resource_class = EntitlementResource
admin.site.register(Entitlement,EntitlementAdmin)
