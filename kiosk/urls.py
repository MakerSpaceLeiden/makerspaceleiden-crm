from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.conf import settings

from acl.models import Machine
from . import views

urlpatterns = [
    path('kiosk', views.kiosk, name='kiosk'),
]
