from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('member/<int:member_id>', views.member_overview, name='overview'),
    path('member/', views.members, name='overview'),

    path('machine/<int:machine_id>', views.machine_overview, name='machine_overview'),
    path('machine/', views.machine_overview, name='machine_overview'),

    # For the trusteeds - to ease admin.
    path('missing_forms/', views.missing_forms, name='missing_forms'),
    path('filed_forms/', views.filed_forms, name='filed_forms'),

    # Convenience page to debug the API
    path('', views.api_index, name='acl-index'),

    # Legacy API
    path('v2', views.api_index_legacy, name='acl-v2'),

    # API oriented
    path('<int:machine_id>', views.api_details, name='details'),
]

