from django.shortcuts import render
from django.urls import path
from revproxy.views import ProxyView

from . import views

urlpatterns = [
    path("", views.index, name="camindex"),
    path("snapshot", views.snapshot, name="snapshot"),
]
