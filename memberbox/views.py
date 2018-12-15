from django.contrib.sites.shortcuts import get_current_site
from django.template import loader
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
import logging


from members.models import User
from .models import Memberbox

@login_required
def index(request):
    context = {
        'title': 'Storage',
        'user' : request.user,
        'has_permission': request.user.is_authenticated,
    }
    return render(request, 'index.html', context)


