from django.shortcuts import render
from django.urls import path
from revproxy.views import ProxyView

from . import views

urlpatterns = [
    path("0.13", views.index, name="spaceapi013"),
]
