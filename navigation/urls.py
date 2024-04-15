from django.urls import path

from navigation.views import NavpageView

urlpatterns = [
    path("navpage/", NavpageView, name="navpage"),
]
