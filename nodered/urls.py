from django.urls import re_path, path
from . import views

urlpatterns = [
    re_path(
        r"^nodered/(?P<url>.*)$", views.NodeRedProxy.as_view(), name="nodered_proxy"
    ),
    path(
        'dashboard/nodered_live_data_and_sensors/', 
        views.NoderedLiveDataAndSensorsView, 
        name='nodered_live_data_and_sensors'
    ),
    path(
        'dashboard/nodered_space_climate/', 
        views.NoderedSpaceClimateView, 
        name='nodered_space_climate'
    ),
]
