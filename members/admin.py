from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import Member, Tag, PermitType, Entitlement

from members.models import Member

class UserResource(resources.ModelResource):
    class Meta:
       model = User
       fields = ('username', 'first_name', 'last_name', 'email','is_active','date_joined')
       import_id_fields = ['username','first_name', 'last_name', 'email']

class MemberResource(resources.ModelResource):
    class Meta:
       model = Member
       fields = ('user', 'form_on_file')
       import_id_fields = [ 'user', 'form_on_file' ]

class TagResource(resources.ModelResource):
    class Meta:
       model = Tag
       fields = [ 'owner', 'tag' ]
       import_id_fields = [ 'owner', 'tag' ]

class EntitlementResource(resources.ModelResource):
    class Meta:
       model = Entitlement
       fields = [ 'permit__name', 'holder__username', 'issuer__username' ]
       fields = [ 'permit', 'holder', 'issuer' ]
       import_id_fields = [ 'permit', 'holder', 'issuer' ]
       # import_id_fields = [ 'permit', 'holder', 'issuer' ]

class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    list_display = ('username','email','form_on_file')

# Define a new User admin
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    inlines = (MemberInline,)
    resource_class = UserResource

# Re-register it in the admin portal - so we get
# to manage the extra bits there.
#
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class MemberAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('user','form_on_file')
    resource_class = MemberResource
admin.site.register(Member,MemberAdmin)

class TagAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    resource_class = TagResource

admin.site.register(Tag,TagAdmin)

class PermitAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('name','description')
admin.site.register(PermitType,PermitAdmin)

class EntitlementAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('permit','holder','issuer')
    resource_class = EntitlementResource
admin.site.register(Entitlement,EntitlementAdmin)
