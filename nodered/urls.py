from django.urls import path, re_path

from . import views

urlpatterns = [
    re_path(
        r"^nodered/(?P<url>.*)$", views.NodeRedProxy.as_view(), name="nodered_proxy"
    ),
    re_path(
        r"^dashboard/(?P<url>.*)$",
        views.NodeRedDashboardProxy.as_view(),
        name="nodered_dashboard_proxy",
    ),
    path(
        "dashboard_intranet/nodered_live_data_and_sensors/",
        views.NoderedLiveDataAndSensorsView,
        name="nodered_live_data_and_sensors",
    ),
    path(
        "dashboard_intranet/nodered_active_machines/",
        views.NoderedActiveMachinesView,
        name="nodered_active_machines",
    ),
]
