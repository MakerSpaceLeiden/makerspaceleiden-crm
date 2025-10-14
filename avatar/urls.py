from django.urls import path

from . import views

# Caveat - not yet behind a @login/bearer protection
urlpatterns = [
    path("<int:pk>", views.index, name="generate-fake-mugshot"),
    path("<path:slug>", views.handle_signed_url, name="generate-fake-mugshot"),
]
