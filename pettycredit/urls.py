from django.urls import path

from . import views

urlpatterns = [
    path("", views.claims, name="claims"),
    # API for the Client-cert based auth variation.
    #
    path("api/v1/claim", views.api1_claim, name="acl-v1-claim"),
    path("api/v1/updateclaim", views.api1_updateclaim, name="acl-v1-updateclaim"),
    path("api/v1/settle", views.api1_settle, name="acl-v1-settle"),
]
