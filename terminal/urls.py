from django.urls import path, register_converter

from makerspaceleiden import converters

from . import views

register_converter(converters.FloatUrlParameterConverter, "float")

urlpatterns = [
    # UI for accepting re-configured terminals or nodes.
    #
    path("forget/<int:pk>", views.forget, name="forget"),
    # API for the Client-cert based auth variation.
    #
    path("api/none", views.api_none, name="api-none"),
    path("api/v2/register", views.api2_register, name="acl-v2-register"),
    path("api/v3/register", views.api3_register, name="acl-v3-register"),
]
