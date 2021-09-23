from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.admin.sites import AdminSite
from django.template import loader
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from makerspaceleiden.decorators import login_or_priveleged, superuser
from django import forms
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from simple_history.admin import SimpleHistoryAdmin
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.forms import widgets

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import datetime
import uuid
import zipfile
import os
import re
from moneyed import Money, EUR
from moneyed.l10n import format_money

def mtostr(m):
   return format_money(m, locale='nl_NL')

import logging
logger = logging.getLogger(__name__)

from .models import PettycashTransaction, PettycashBalanceCache
from .admin import PettycashBalanceCacheAdmin, PettycashTransactionAdmin
from .forms import PettycashTransactionForm
from members.models import User

# Note - we do this here; rather than in the model its save() - as this
# lets admins change things through the database interface silently. 
# Which can help when sheparding the community.
#
def alertOwnersToChange(items, userThatMadeTheChange = None, toinform = []):
    context = {
           'user': userThatMadeTheChange,
           'base': settings.BASE,
    }
    if userThatMadeTheChange:
      toinform.append(userThatMadeTheChange.email)

    if settings.ALSO_INFORM_EMAIL_ADDRESSES:
       toinform.extend(settings.ALSO_INFORM_EMAIL_ADDRESSES)

    return emailPettycashInfo(items, 'email_notification', toinform = [], context = {})

def pettycash_redirect(pk = None):
    url = reverse('balances')
    if pk:
      url = '{}#{}'.format(url, pk)
    return redirect(url)

def transact(request,label,src=None,dst=None,description=None,amount=None,reason=None):
    form = PettycashTransactionForm(request.POST or None, initial = { 'src': src, 'dst': dst, 'description': description, 'amount': amount })
    if form.is_valid():
        try:
            item = form.save(commit = False)

            if not item.description:
                item.description = "Entered by {}".format(request.user)

            item._change_reason = "Logged in as {}, {}.".format(request.user, reason)
            item.save()

            # alertOwnersToChange(item, request.user, [ item.owner.email ])
            return pettycash_redirect(item.id)

        except Exception as e:
            logger.error("Unexpected error during initial save of new pettycash: {}".format(e))

        return HttpResponse("Something went wrong ??",status=500,content_type="text/plain")
 
    if src:
        form.fields['src'].widget = widgets.HiddenInput()
    if dst:
        form.fields['dst'].widget = widgets.HiddenInput()

    context = {
        'title': label,
        'form': form,
        'action': 'Pay',
        }
    return render(request, 'pettycash/invoice.html', context)


@login_required
def index(request,days=30):
    lst = PettycashBalanceCache.objects.all()
    context = {
        'title': 'Balances',
        'lst': lst,
        'settings': settings,
       }
    return render(request, 'pettycash/index.html', context)

@login_required
@login_or_priveleged
def invoice(request,src):
    try:
       src= User.objects.get(id=src)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")

    return transact(request,'%s to pay to %s ' % (src, settings.POT_LABEL), src=src, dst=settings.POT_ID, reason="Invoice via website")

@login_required
@login_or_priveleged
def transfer(request,src,dst):
    try:
       src = User.objects.get(id=src)
       dst = User.objects.get(id=dst)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")

    dst_label = dst
    if dst.id == settings.POT_ID:
       dst_label = settings.POT_LABEL

    return transact(request,'%s to pay %s' % (src,dst_label), src=src, dst=dst, reason="Transfer form website")

@superuser
def deposit(request,dst):
    try:
      dst = User.objects.get(id=dst)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")

    dst_label = dst
    if dst.id == settings.POT_ID:
       dst_label = settings.POT_LABEL

    return transact(request,'Deposit into account %s' % (dst_label), dst=dst,src=settings.POT_ID, reason="Deposit via website")

@login_required
def pay(request):
    amount_str = request.GET.get('amount', None)
    description =  request.GET.get('description', None)

    if not amount_str and not description:
        return HttpResponse("Amount/Description parameters mandatory",status=400,content_type="text/plain")
    amount = Money(amount_str, EUR)

    return transact(request,"%s pays %s to the Makerspace" % (mtostr(amount), request.user), src=request.user,dst=settings.POT_ID,amount=amount,description=description, reason="Pay via website")

@login_required
def showtx(request,pk):
    try:
       tx = PettycashTransaction.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")

    context = {
        'title': 'Details transaction %s @ %s' % (tx.id, tx.date),
        'tx': tx,
	'settings': settings,
        }
    return render(request, 'pettycash/details.html', context)


@login_required
def show(request,pk):
    try:
       user = User.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")
    balance = None
    lst = []
    moneys_in = 0 # Money(0,EUR)
    moneys_out = 0 # Money(0,EUR)
    try:
       balance = PettycashBalanceCache.objects.get(owner=user)
       lst= PettycashTransaction.objects.all().filter(Q(src=user) | Q(dst=user)).order_by('id')
       for tx in lst:
           if tx.dst == user:
              moneys_in += tx.amount
           else:
             moneys_out += tx.amount
    except ObjectDoesNotExist as e:
       pass

    label = user
    if user.id == settings.POT_ID:
       label = settings.POT_LABEL

    context = {
        'title': 'Balance and transactions for %s' % (label),
        'balance': balance,
	'who': user,
        'lst': lst,
	'in': moneys_in,
	'out': moneys_out,
        }
    return render(request, 'pettycash/view.html', context)


