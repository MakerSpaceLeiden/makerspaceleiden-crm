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
from django.middleware.csrf import CsrfViewMiddleware


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
from .forms import PettycashTransactionForm, PettycashDeleteForm, PettycashPairForm, CamtUploadForm, ImportProcessForm
from .models import pemToSHA256Fingerprint, hexsha2pin
from .camt53 import camt53_process

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
    url = reverse('mytransactions')
    if pk:
      url = '{}#{}'.format(url, pk)
    return redirect(url)

def transact_raw(request,src=None,dst=None,description=None,amount=None,reason=None,user=None):
    if None in [ src, dst, description, amount, reason, user ]:
        logger.error("Transact raw called with missing arguments. bug.")
        return 0

    try:
        tx = PettycashTransaction(src=src,dst=dst,description=description,amount=amount)
        logger.error("Info: %s" % reason)
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

        if item.amount < Money(0,EUR) or item.amount > settings.MAX_PAY_API:
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

    products = None
    if dst == settings.POT_ID:
        products = PettycashSku.objects.all()
    
    context = {
        'title': label,
        'form': form,
        'action': 'Pay',
        'products' : products
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
def qrcode(request):
    description =  request.GET.get('description', None)
    amount_str = request.GET.get('amount', 0)
    # LR: A bit ugly but money will produce amounts with a comma.
    amount_str = amount_str.replace(',', '.')
    amount = Money(amount_str, EUR)

    context = {
        'title': 'QR code',
        'description': description,
        'amount' : amount,
        'url' : "%s?description=%s&amount=%s" % (request.build_absolute_uri('/pettycash/pay'), description, amount_str)
    }
    return render(request, 'pettycash/qrcode.html', context)

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
def transfer_to_member(request,src):

    src = request.user
    description = "Transfer"
    amount = Money(0)
    form = PettycashTransactionForm(request.POST or None, initial = { 'src': src, 'description': description, 'amount': amount })

    if form.is_valid():
        reason = "Transfer"
        item = form.save(commit = False)
        if transact_raw(request, src=item.src,dst=item.dst,description=item.description,amount=item.amount,reason="Logged in as {}, {}.".format(request.user, reason),user=request.user):
            return pettycash_redirect(item.id)

    if src:
        form.fields['src'].widget = widgets.HiddenInput()

    context = {
        'form': form
    }

    return render(request, 'pettycash/transfer_to_member.html', context)

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
    lst = PettycashTerminal.objects.all().filter(Q(accepted = True) & Q(station = None))
    unlst = PettycashTerminal.objects.all().filter(Q(accepted = False))
    paired = PettycashStation.objects.all().filter(~Q(terminal = None))
    unpaired = PettycashStation.objects.all().filter(Q(terminal = None))
    context = {
        'title': 'Assigning terminal',
        'lst': lst,
        'unlst': unlst,
        'paired': paired,
        'unpaired': unpaired,
        'settings': settings,
       }
    return render(request, 'pettycash/unpaired.html', context)

@superuser
def cam53upload(request):
    if request.method == 'POST':
        form = CamtUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
               file = request.FILES['cam53file']
               print(file)
               txs = camt53_process(file)
                
               valids = any(d['success'] for d in txs)

               ids = []
               for tx in txs:
                   if tx['success']:
                      ids.append({ 'description' : tx['description'], 'user': tx['user'], 'amount': tx['amount'], 
                          'change_reason': "TXREF=%s HOLDER=%s IBAN=%s import, ran by %s" % (tx['ref'], tx['name_str'],tx['iban_str'], request.user ) })

               okf = ImportProcessForm(ids) # list(map(lambda x: x['id'], txs)))

               context = { 'title': 'Import log', 'settings': settings, 'txs': txs, 'valids': valids, 'form': okf, 'action': 'Deposit for real' }
               return render(request, 'pettycash/importlog.html', context)
 
            except Exception as e:
                return HttpResponse("FAIL: %s" % e,status=500,content_type="text/plain")

            # Redirect to the document list after POST
            return HttpResponse("Unknown FAIL",status=500,content_type="text/plain")
    else:
        form = CamtUploadForm() # A empty, unbound form

    context = {
        'title': 'Upload CAM53 transactions',
	'settings': settings,
        'form': form,
        'action': 'upload',
        }
    return render(request,'pettycash/upload.html', context)

@superuser
def cam53process(request):
    if request.method != 'POST':
       return HttpResponse("Unknown FAIL",status=400,content_type="text/plain")

    reason = CsrfViewMiddleware().process_view(request, None, (), {})
    if reason:
       return HttpResponse("CSRF FAIL",status=400,content_type="text/plain")

    ok = []
    failed= []
    skipped = []
    vals = request.POST.dict()
    for i in range(int(vals['vals'])):
      try:
          if vals.get('ok_%d' % i,'off') == 'on':
               user = User.objects.get(id = vals['user_%d' % i])
               amount = Money(vals['amount_%d' % i], EUR)
               tx = PettycashTransaction(src=User.objects.get(id = settings.POT_ID), dst=user, amount=amount)
               tx.description = vals['description_%d' % i]
               tx._change_reason = vals['change_reason_%d' % i]
               tx.save()
               alertOwnersToChange(tx, request.user, [ tx.src.email, tx.dst.email ], "Banking transaction processed; %s deposited" % tx.amount, 'deposit_tx.txt')
               ok.append(tx)
          else:
               skipped.append('%s: %s' % (vals.get('description_%d' % i, "??"), vals.get('amount_%d' % i, "??")))
      except Exception as e:
         failed.append('%d: %s %s: %s<br>%s' % (i, vals.get('change_reason_%d' % i, "??"), vals.get('description_%d' % i, "??"), vals.get('amount_%d' % i, "??"),e))

    context = { 'title': 'Import Results', 'settings': settings, 'ok': ok, 'failed': failed, 'skipped': skipped }
    return render(request, 'pettycash/importlog-results.html', context)

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
def show_mine(request):
    user = request.user
    balance = 0
    lst = []

    try:
       balance = PettycashBalanceCache.objects.get(owner=user)
       lst = PettycashTransaction.objects.all().filter(Q(src=user) | Q(dst=user)).order_by('id')
    except ObjectDoesNotExist as e:
        pass

    context = {
        'title': 'SpaceTegoed',
        'balance': balance,
    	'who': user,
        'lst': lst
    }

    return render(request, 'pettycash/view_mine.html', context)

@login_required
def manual_deposit(request):
    topup = settings.PETTYCASH_TOPUP
    try:
        balance = PettycashBalanceCache.objects.get(owner=request.user)
        topup = int((-float(balance.balance.amount) + settings.PETTYCASH_TOPUP)/5+0.5) * 5;
    except ObjectDoesNotExist as e:
       pass

    context = {
        'title': 'Perform a manual deposit',
        'settings' : settings,
        'user': request.user,
        # String according to Quick Response Code richtlijnen van de Europese Betalingsraad (EPC). 
        # See: https://epc-qr.eu. We need to do this here; rather than in the template; as the
        # latter does not allow for for line breaks (qr_from_text).
        #
        'epc' :	 "BCD\n002\n1\nSCT\n\n%s\n%s\nEUR%.2f\n\n\nStorting Spacepot %s / %s\n" % (
              settings.PETTYCASH_TNS, settings.PETTYCASH_IBAN, topup, request.user.pk, request.user
	)
    }

    return render(request, 'pettycash/manual_deposit.html', context)


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
    # LR: A bit ugly but money will produce amounts with a comma.
    amount_str = amount_str.replace(',', '.')
    description =  request.GET.get('description', None)

    if not amount_str and not description:
        return HttpResponse("Amount/Description parameters mandatory",status=400,content_type="text/plain")
    amount = Money(amount_str, EUR)

    return transact(request,"%s pays %s to the Makerspace for %s" % (request.user, mtostr(amount), description), src=request.user,dst=settings.POT_ID,amount=amount,description=description, reason="Pay via website")

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
        #tx.delete();
        tx.refund_booking()
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
               reason="via API; tagid=%s (%s) @%s" % (tag.id,tag.owner,node) ,user=tag.owner):
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

    # 1. We're always offered an x509 client cert.
    #
    cert = request.META.get('SSL_CLIENT_CERT', None)
    if cert == None:
       logger.error("Bad request, missing cert")
       return HttpResponse("No client identifier, rejecting",status=400,content_type="text/plain")

    client_sha = pemToSHA256Fingerprint(cert)
    server_sha = pemToSHA256Fingerprint(request.META.get('SSL_SERVER_CERT'))

    # 2. If we do not yet now this cert - add its fingrerprint to the database
    #    and mark it as pending. Return a secret/nonce.
    #
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

    # 3. If this is a new terminal; check that it has the right nonce from the initial
    #    exchange; and verify that it knows a secret (the tag id of an admin). If so
    #    auto approve it.
    #
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
            m.update(bytes.fromhex(client_sha))
            m.update(bytes.fromhex(server_sha))
            sha = m.hexdigest()
            if sha.lower() == response.lower():
                terminal.accepted = True
                terminal._change_reason = "Terminal %s, IP=%s was activated by tag %d of %s" % (terminal, ip, tag.id, tag.owner)
                terminal.save()
                logger.info("Terminal %s accepted, tag swipe by %s matched." % (terminal, tag.owner))

                # proof to the terminal that we know the tag too. This prolly 
                # should be an HMAC
                #
                m = hashlib.sha256()
                m.update(tag.tag.encode('ascii'))
                m.update(bytes.fromhex(sha))
                sha = m.hexdigest()
                return HttpResponse(sha,status=200,content_type="text/plain")

         logger.error("Nonce & fingerprint ok; but response could not be correlated to a tag (%s, ip=%si)" % (terminal, ip))
         return HttpResponse("Pairing failed",status=400,content_type="text/plain")

    # 4. We're talking to an approved terminal - give it its SKU list if it has
    #    been wired to a station; or just an empty list if we do not know yet.
    #
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
