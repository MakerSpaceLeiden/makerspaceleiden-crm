from django.urls import path
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.index, name='members-index'),
]

