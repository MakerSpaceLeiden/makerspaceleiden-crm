from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('member/<int:member_id>', views.member_overview, name='overview'),
    path('member/', views.members, name='overview'),

    path('tag/edit/<int:tag_id>', views.tag_edit, name='tag_edit'),
    path('tag/delete/<int:tag_id>', views.tag_delete, name='tag_delete'),

    path('machine/<int:machine_id>', views.machine_overview, name='machine_overview'),
    path('machine/', views.machine_overview, name='machine_overview'),

    # For the trusteeds - to ease admin.
    path('missing_forms/', views.missing_forms, name='missing_forms'),
    path('filed_forms/', views.filed_forms, name='filed_forms'),

    # Convenience page to debug the API
    path('', views.api_index, name='acl-index'),

    # API oriented
    path('api/v1/getok/<str:machine>', views.api_getok, name='acl-v1-getok'),
    path('api/v1/gettaginfo', views.api_gettaginfo, name='acl-v1-gettaginfo'),

    path('<int:machine_id>', views.api_details, name='details'),
]

