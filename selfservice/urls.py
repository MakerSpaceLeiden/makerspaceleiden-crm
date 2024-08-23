from django.conf import settings
from django.urls import include, path, re_path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("record_instructions/", views.recordinstructions, name="add_instruction"),
    path("userdetails/", views.userdetails, name="userdetails"),
    path(
        "userdetails/edit/<int:user_id>",
        views.userdetails_admin_edit,
        name="userdetails_admin_edit",
    ),
    path("waiverform/", views.waiverformredir, name="waiverformredir"),
    path("waiver/<int:user_id>/form", views.waiverform, name="waiverform"),
    path(
        "waiver/<int:user_id>/confirm", views.confirm_waiver, name="waiver_confirmation"
    ),
    # Telegram BOT
    path("telegram/connect", views.telegram_connect, name="telegram_connect"),
    path("telegram/disconnect", views.telegram_disconnect, name="telegram_disconnect"),
    path("signal/disconnect", views.signal_disconnect, name="signal_disconnect"),
    path(
        "notifications/settings",
        views.notification_settings,
        name="notification_settings",
    ),
    path(
        "notifications/settings/signal",
        views.save_signal_notification_settings,
        name="signal_notification_settings",
    ),
    path(
        "notifications/settings/email",
        views.save_email_notification_settings,
        name="email_notification_settings",
    ),
    path("notifications/test", views.notification_test, name="notification_test"),
    path("space_state", views.space_state, name="space_state"),
    path("space_state/checkout", views.space_checkout, name="checkout_from_space"),
    path("api/v1/state", views.space_state_api, name="space_state_api"),
    path("api/v1/info", views.space_state_api_info, name="space_state_api_info"),
    # For the trutee's -- to ease admin
    path("pending/", views.pending, name="pending"),
    path("send_reset_email/<int:uid>", views.send_reset_email, name="send_reset_email"),
    # path('confirm_email/', views.userdetails, name='confirm_email'),
    path(
        "confirm_email/<uidb64>/<token>/<new_email>",
        views.confirmemail,
        name="confirm_email",
    ),
    # for the password reset by email.
    re_path(
        "^registration/", include("django.contrib.auth.urls"), name="password_reset"
    ),
]

if settings.GRAND_AMNESTY:
    urlpatterns.append(path("amnety", views.amnesty, name="amnesty"))
