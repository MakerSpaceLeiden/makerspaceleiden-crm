from django.urls import path, re_path

from . import views

urlpatterns = [
    path("kwh/", views.kwh_view, name="kwh_view"),
    re_path(r"^crm/kwh/(?P<path>.*)$", views.kwh_proxy, name="kwh_proxy"),
]
