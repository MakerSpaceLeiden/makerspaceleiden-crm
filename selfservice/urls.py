from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy

from acl.models import Machine
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('record_instructions/', views.recordinstructions, name='add_instruction'),
    path('userdetails/', views.userdetails, name='userdetails'),
    path('pending/', views.pending, name='pending'),

    # path('confirm_email/', views.userdetails, name='confirm_email'),
    path('confirm_email/<uidb64>/<token>/<newemail>', views.confirmemail, name='confirm_email'),

    path('signup/', views.signup, name='signup'),

    # for the password reset by email.
    re_path('^registration/', include('django.contrib.auth.urls'), name='password_reset'),
]

