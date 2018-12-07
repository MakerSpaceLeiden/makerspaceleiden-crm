from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('overview/<int:member_id>', views.member_overview, name='overview'),
    path('missing_forms/', views.missing_forms, name='missing_forms'),
    path('filed_forms/', views.filed_forms, name='filed_forms'),
    path('overview/', views.overview, name='overview'),
    path('<int:machine_id>', views.details, name='details'),
    path('', views.index, name='index'),
]

