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
from django.http import JsonResponse


from django.views.decorators.csrf import csrf_exempt
from makerspaceleiden.decorators import superuser_or_bearer_required

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import datetime
import uuid
import zipfile
import os
import re
import secrets
import hashlib
from django.utils import timezone

from moneyed import Money, EUR
from moneyed.l10n import format_money

def mtostr(m):
   return format_money(m, locale='nl_NL')

def client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

import logging
logger = logging.getLogger(__name__)

from .models import PettycashTransaction, PettycashBalanceCache, PettycashSku, PettycashTerminal, PettycashStation
from .admin import PettycashBalanceCacheAdmin, PettycashTransactionAdmin
from .forms import PettycashTransactionForm, PettycashDeleteForm, PettycashPairForm

from .models import pemToSHA256Fingerprint, hexsha2pin
from members.models import User, Tag

# Note - we do this here; rather than in the model its save() - as this
# lets admins change things through the database interface silently. 
# Which can help when sheparding the community.
#
def alertOwnersToChange(tx, userThatMadeTheChange = None, toinform = [], reason=None, template = 'email_tx.txt' ):
    src_label = "%s" % tx.src
    dst_label = "%s" % tx.dst
    label = dst_label

    if tx.src.id == settings.POT_ID:
        src_label = settings.POT_LABEL
    else:
        toinform.append(tx.src.email)

    if tx.dst.id == settings.POT_ID:
        dst_label = settings.POT_LABEL
        label = src_label
    else:
        toinform.append(tx.dst.email)

    context = {
           'user': userThatMadeTheChange,
           'base': settings.BASE,
           'reason': reason,
           'tx': tx,
           'src_label' : src_label,
           'dst_label' : dst_label,
           'label' : label,
           'settings': settings,
    }

    if userThatMadeTheChange.email not in toinform:
        toinform.append(userThatMadeTheChange.email)

    # if settings.ALSO_INFORM_EMAIL_ADDRESSES:
    #    toinform.extend(settings.ALSO_INFORM_EMAIL_ADDRESSES)

    subject = render_to_string('subject_%s' % template, context).strip()
    message = render_to_string(template, context)

    return EmailMessage(subject, message, to=toinform, from_email=settings.DEFAULT_FROM_EMAIL).send()

def pettycash_redirect(pk = None):
    url = reverse('balances')
    if pk:
      url = '{}#{}'.format(url, pk)
    return redirect(url)

def transact_raw(request,src=None,dst=None,description=None,amount=None,reason=None,user=None):
    if None in [ src, dst, description, amount, reason, user ]:
        logger.error("Transact raw called with missing arguments. bug.")
        return 0

    try:
        tx = PettycashTransaction(src=src,dst=dst,description=description,amount=amount)
        tx._change_reason = reason
        tx.save()
        alertOwnersToChange(tx, user, [])

    except Exception as e:
        logger.error("Unexpected error during initial save of new pettycash: {}".format(e))
        return 0

    return 1
    
def transact(request,label,src=None,dst=None,description=None,amount=None,reason=None):
    form = PettycashTransactionForm(request.POST or None, initial = { 'src': src, 'dst': dst, 'description': description, 'amount': amount })
    if form.is_valid():
        item = form.save(commit = False)

        if item.amount < Money(0,EUR)  or item.amount > settings.MAX_PAY_API:
           if not request.user.is_privileged:
              return HttpResponse("Only transactions between %s and %s" % (Money(0,EUR), settings.MAX_PAY_API), status=406,content_type="text/plain")
           logger.info("Allowing super user perms to do a non compliant transaction %s" % (item))

        if not item.description:
             item.description = "Entered by {}".format(request.user)

        if transact_raw(request, src=item.src,dst=item.dst,description=item.description,amount=item.amount,reason="Logged in as {}, {}.".format(request.user, reason),user=request.user):
             return pettycash_redirect(item.id)

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
    prices = PettycashSku.objects.all()
    context = {
        'title': 'Balances',
        'lst': lst,
        'settings': settings,
        'pricelist': prices,
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

@login_required
def unpaired(request):
    lst = PettycashTerminal.objects.all().filter(Q(accepted = False) | Q(station = None))
    paired = PettycashStation.objects.all().filter(~Q(terminal = None))
    unpaired = PettycashStation.objects.all().filter(Q(terminal = None) & Q(activated = True))
    context = {
        'title': 'Unpaired terminals',
        'lst': lst,
        'paired': paired,
        'unpaired': unpaired,
        'settings': settings,
       }
    return render(request, 'pettycash/unpaired.html', context)

@superuser
def pair(request,pk):
    try:
       tx = PettycashTerminal.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")

    form = PettycashPairForm(request.POST or None)
    if form.is_valid():
        station = form.cleaned_data['station']
        reason = "%s. %s paired to %s (by %s)" % (form.cleaned_data['reason'], tx, station, request.user)

        tx.accepted = True
        tx._change_reason = reason
        tx.save()

        station.terminal = tx
        station._change_reason = reason
        station.save()

        return redirect('unpaired')

    context = {
        'title': 'Pair %s' % (tx.name),
        'tx': tx,
	'settings': settings,
        'form': form,
        'user': request.user,
        'action': 'pair',
        }

    return render(request, 'pettycash/pair.html', context)

@csrf_exempt
@superuser_or_bearer_required
def api_pay(request):
    try: 
       node = request.GET.get('node', None)
       tagstr = request.GET.get('src', None)
       amount_str = request.GET.get('amount', None)
       description =  request.GET.get('description', None)
       amount = Money(amount_str, EUR)
    except Exception as e:
        logger.error("Tag %s payment has param issues." % (tagstr) )
        return HttpResponse("Params problems",status=400,content_type="text/plain")

    if None in [ tagstr, amount_str, description, amount, node ]:
        logger.error("Missing param, Payment Tag %s denied" % (tagstr) )
        return HttpResponse("Mandatory params missing",status=400,content_type="text/plain")

    if amount < Money(0,EUR):
        logger.error("Invalid param. Payment Tag %s denied" % (tagstr) )
        return HttpResponse("Invalid param",status=400,content_type="text/plain")

    if amount > settings.MAX_PAY_API:
        logger.error("Payment too high, rejected, Tag %s denied" % (tagstr) )
    pass

@superuser
def deposit(request,dst):
    try:
      dst = User.objects.get(id=dst)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")

    dst_label = dst
    if dst.id == settings.POT_ID:
       dst_label = settings.POT_LABEL

    return transact(request,'Deposit into account %s' % (dst_label), dst=dst,src=settings.POT_ID, reason="Deposit via website", description = "Deposit" )

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

@login_required
def pay(request):
    amount_str = request.GET.get('amount', None)
    description =  request.GET.get('description', None)

    if not amount_str and not description:
        return HttpResponse("Amount/Description parameters mandatory",status=400,content_type="text/plain")
    amount = Money(amount_str, EUR)

    return transact(request,"%s pays %s to the Makerspace" % (mtostr(amount), request.user), src=request.user,dst=settings.POT_ID,amount=amount,description=description, reason="Pay via website")

@login_required
def delete(request, pk):
    try:
       tx = PettycashTransaction.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        return HttpResponse("Not found",status=404,content_type="text/plain")

    if request.user != tx.src and request.user != tx.dst and not request.user.is_privileged:
        return HttpResponse("Not allowed (you can only delete your own payments.",status=404,content_type="text/plain")

    form = PettycashDeleteForm(request.POST or None)
    if form.is_valid():
        reason = "%s (by %s)" % (form.cleaned_data['reason'], request.user)
        tx._change_reason = reason
        tx.delete();
        alertOwnersToChange(tx, request.user, [ tx.src.email, tx.dst.email ], reason , 'delete_tx.txt')
        return redirect('transactions', pk = request.user.id)

    context = {
        'title': 'Delete transaction %s @ %s' % (tx.id, tx.date),
        'tx': tx,
	'settings': settings,
        'form': form,
        'user': request.user,
        'action': 'delete',
        }

    return render(request, 'pettycash/delete.html', context)

@csrf_exempt
@superuser_or_bearer_required
def api_pay(request):
    try: 
       node = request.GET.get('node', None)
       tagstr = request.GET.get('src', None)
       amount_str = request.GET.get('amount', None)
       description =  request.GET.get('description', None)
       amount = Money(amount_str, EUR)
    except Exception as e:
        logger.error("Tag %s payment has param issues." % (tagstr) )
        return HttpResponse("Params problems",status=400,content_type="text/plain")

    if None in [ tagstr, amount_str, description, amount, node ]:
        logger.error("Missing param, Payment Tag %s denied" % (tagstr) )
        return HttpResponse("Mandatory params missing",status=400,content_type="text/plain")

    if amount < Money(0,EUR):
        logger.error("Invalid param. Payment Tag %s denied" % (tagstr) )
        return HttpResponse("Invalid param",status=400,content_type="text/plain")

    if amount > settings.MAX_PAY_API:
        logger.error("Payment too high, rejected, Tag %s denied" % (tagstr) )
        return HttpResponse("Payment Limit exceeded",status=400,content_type="text/plain")

    try:
         tag = Tag.objects.get(tag = tagstr)
    except ObjectDoesNotExist as e:
         logger.error("Tag %s not found, denied" % (tagstr) )
         return HttpResponse("Tag not found",status=404,content_type="text/plain")

    if transact_raw(request,src=tag.owner,dst=User.objects.get(id = settings.POT_ID),description=description,amount=amount,
               reason="Payment via API; tagid=%s (owned by %s) from payment node:  %s" % (tag.id,tag.owner,node) ,user=tag.owner):
        label = "%s" % tag.owner.first_name
        if len(label) < 1:
           label = "%s" % tag.owner.last_name
        if len(label) < 1:
           label = "%s" % tag.owner
        return JsonResponse({ 'result': True, 'amount': amount.amount, 'user': label})

    return HttpResponse("FAIL",status=500,content_type="text/plain")

@csrf_exempt
def api_register(request):
    ip = client_ip(request)

    cert = request.META.get('SSL_CLIENT_CERT', None)
    if cert == None:
       return HttpResponse("No client identifier, rejecting",status=400,content_type="text/plain")

    client_sha = pemToSHA256Fingerprint(cert)
    server_sha = pemToSHA256Fingerprint(request.META.get('SSL_SERVER_CERT'))

    try:
        terminal = PettycashTerminal.objects.get(fingerprint = client_sha)

    except ObjectDoesNotExist as e:
         logger.info("Fingerprint %s not found, adding to the list of unknowns" % client_sha)

         name = request.GET.get('name', None)
         if not name:
             logger.error("Bad request, missing name for %s at %s" % (client_sha, ip))
             return HttpResponse("Bad request, missing name",status=400,content_type="text/plain")

         terminal = PettycashTerminal(fingerprint = client_sha, name = name, accepted = False)
         terminal.nonce = secrets.token_hex(32)
         terminal.accepted = False
         terminal._change_reason = 'Added on first contact; from IP address %s' %( ip )
         terminal.save()

         logger.info("Issuing first time nonce to %s at %s" % (client_sha, ip))
         return HttpResponse(terminal.nonce,status=401,content_type="text/plain")

    if not terminal.accepted:
         cutoff = timezone.now() - datetime.timedelta(minutes=settings.PAY_MAXNONCE_AGE_MINUTES)
         if cutoff > terminal.date:
             logger.info("Fingerprint %s known, but too old. Issuing new one." % client_sha)
             terminal.nonce = secrets.token_hex(32)
             terminal.date = timezone.now()
             terminal._change_reason = "Updating nonce, repeat register; but the old one was too old."
             terminal.save()
             logger.info("Updating nonce for  %s at %s" % (client_sha, ip))
             return HttpResponse(terminal.nonce,status=401,content_type="text/plain")

         response= request.GET.get('response', None)
         if not response:
             logger.error("Bad request, missing response for %s at %s" % (client_sha, ip))
             return HttpResponse("Bad request, missing response",status=400,content_type="text/plain")

         # This response should be the SHA256 of nonce + tag + client-cert-sha256 + server-cert-256.
         # and the tag should be owned by someone whcih has the right admin rights.
         #
         for tag in Tag.objects.all().filter(owner__groups__name = settings.PETTYCASH_ADMIN_GROUP):
            m = hashlib.sha256()
            m.update(terminal.nonce.encode('ascii'))
            m.update(tag.tag.encode('ascii'))
            m.update(client_sha.encode('ascii'))
            m.update(server_sha.encode('ascii'))
            if m.hexdigest() == response:
                terminal.accepted = True
                terminal._change_reason = "Terminal %s, IP=%s was activated by tag %d of %s" % (terminal, ip, tag.id, tag.owner)
                terminal.save()
                logger.info("Terminal %s accepted, tag swipe by %s matched." % (terminal, tag.owner))
                return HttpResponse("OK",status=200,content_type="text/plain")

         logger.error("Nonce & fingerprint ok; but response could not be correlated to a tag (%s, ip=%si)" % (terminal, ip))
         return HttpResponse("Pairing failed",status=400,content_type="text/plain")

    try:
         station = PettycashStation.objects.get(terminal = terminal)
    except ObjectDoesNotExist as e:
         return JsonResponse({})

    avail = []
    for item in station.available_skus.all():
         avail.append({ 
             'name': item.name, 
             'description': item.description, 
             'price': item.amount.amount,
             'default': item == station.default_sku
         })

    return JsonResponse({
        'name':		terminal.name,
        'description':	station.description,
        'pricelist':	avail,
    }, safe = False)

@csrf_exempt
def api_get_skus(request):
    out =[]
    for item in PettycashSku.objects.all():
       out.append({ 'name': item.name, 'description': item.description, 'price': item.amount.amount })
    
    return JsonResponse(out, safe=False)

@csrf_exempt
def api_get_sku(request,sku):
    try:
       item = PettycashSku.objects.get(pk=sku)
       return JsonResponse({ 'id': item.pk,  'name': item.name, 'description': item.description, 'price': float(item.amount.amount) })
    except ObjectDoesNotExist as e:
         logger.error("SKU %d not found, denied" % (sku) )
         return HttpResponse("SKU not found",status=404,content_type="text/plain")
    
    return HttpResponse("Error",status=500,content_type="text/plain")
