from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('mailinglists_edit/<int:user_id>', views.mailinglists_edit , name='mailinglists_edit'),
    path('mailinglists_edit', views.mailinglists_edit , name='mailinglists_edit'),
]
