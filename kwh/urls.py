from django.urls import re_path

from . import views

urlpatterns = [
    re_path("(?P<path>.*)", views.kwh_proxy, name="kwh"),
]
