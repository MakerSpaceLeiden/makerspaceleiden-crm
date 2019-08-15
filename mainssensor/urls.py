from django.shortcuts import render
from django.urls import path

from . import views

urlpatterns = [
    path('api/v1/mainssensor/resolve/<int:tag>', views.resolve, name='resolve'),
    path('api/v1/mainssensor/resolve', views.resolve, name='resolve'),
    path('mainsensors', views.index, name='mainsindex'),
]
