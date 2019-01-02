from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('member/<int:member_id>', views.member_overview, name='overview'),
    path('member/', views.members, name='overview'),

    path('machine/<int:machine_id>', views.machine_overview, name='machine_overview'),
    path('machine/', views.machine_overview, name='machine_overview'),

    path('missing_forms/', views.missing_forms, name='missing_forms'),
    path('filed_forms/', views.filed_forms, name='filed_forms'),

    # API oriented
    path('<int:machine_id>', views.api_details, name='details'),
    path('', views.api_index, name='acl-index'),
]

