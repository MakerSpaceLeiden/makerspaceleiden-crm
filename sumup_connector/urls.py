from django.urls import path

from . import views

urlpatterns = [
    # End user interaction
    path("", views.index, name="sumup-index"),
    # APIs for the payment terminals
    path("api/v1/sumup-pay", views.api1_sumup_pay, name="sumup-v1-pay"),
    # External callback - called by SumUP from the internet.
    path(
        "api/v1/sumup-callback/<int:sumup_pk>-<int:timeint>-<str:hash>",
        views.api1_sumup_callback,
        name="sumup-v1-callback",
    ),
]
