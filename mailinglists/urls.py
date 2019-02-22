from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('mailinglists_edit', views.mailinglists_edit , name='mailinglists_edit'),
]
