from django.urls import path

from . import views

urlpatterns = [
    path("api/v1/sumup-pay", views.api1_sumup_pay, name="sumup-v1-pay"),
    path("api/v1/sumup-callback/<int:sumup_pk>-<int:timeint>-<str:hash>", views.api1_sumup_callback, name="sumup-v1-callback"),
]
