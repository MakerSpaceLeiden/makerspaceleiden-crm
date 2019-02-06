from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('member/<int:member_id>', views.member_overview, name='overview'),
    path('member/', views.members, name='overview'),

    path('tag/<int:tag_id>', views.tag_edit, name='tag_edit'),

    path('machine/<int:machine_id>', views.machine_overview, name='machine_overview'),
    path('machine/', views.machine_overview, name='machine_overview'),

    # For the trusteeds - to ease admin.
    path('missing_forms/', views.missing_forms, name='missing_forms'),
    path('filed_forms/', views.filed_forms, name='filed_forms'),

    # Convenience page to debug the API
    path('', views.api_index, name='acl-index'),

    # Legacy API
    path('v1', views.api_index_legacy1, name='acl-v1'),
    path('v1/<str:secret>', views.api_index_legacy1, name='acl-v1'),
    path('v2', views.api_index_legacy2, name='acl-v2'),

    # API oriented
    path('<int:machine_id>', views.api_details, name='details'),
]

