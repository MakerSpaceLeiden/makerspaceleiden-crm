import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from moneyed import EUR, Money

from makerspaceleiden.mail import emailPlain, emails_for_group
from members.models import User
from terminal.decorators import is_paired_terminal

from .models import PettycreditClaim, PettycreditClaimChange

logger = logging.getLogger(__name__)

def email_fail(
    terminal=None,
    user=None,
    claim=None,
    error="Unknown",
    args=None,
    subject="Error during SumUP paument",
):
    admins = emails_for_group(settings.PETTYCASH_ADMIN_GROUP)
    if user and user.email:
        admins.append(user.email)
    else:
        if claim is not None and claim.src is not None and claim.src.email is not None:
            admins.append(claim.src.email)
    emailPlain(
        "sumup/email_fail.txt",
        toinform=admins,
        context={"error": error, "args": args, "claim": claim, "subject": subject},
    )


@csrf_exempt
@is_paired_terminal
def api1_sumup_pay(request, terminal):
    if not request.POST:
        logger.error(f"api1_sumup_pay: expected POST, got {request.method}")
        return HttpResponse("Bad request", status=400, content_type="text/plain")

    p = {}
    for f in ['userid','amount']:
        if not f in request.POST:
            logger.error(f"api1_sumup_pay: param {f} missing")
            return HttpResponse("Missing param", status=422, content_type="text/plain")
	p[f] = " ".request.POST.getlist(f)

    try:
        member = User.objects.get(pk=p['userid'])
        amount = Money(float(amount), EUR)
    except Exception as e:
        logger.error(f"api1_sumup_pay could process data: {e}")
        return HttpResponse("Missing param", status=422, content_type="text/plain")

    try:
        checkout = Checkout(user=member, amount=amount)
        checkout.transact(terminal = terminal)
    except Exception as e:
        logger.error(f"api1_sumup_pay could transact: {e}")
        return HttpResponse("Server error", status=500, content_type="text/plain")

    return HttpResponse("OK");

@csrf_exempt
def api1_sumup_callback(request,sumup_pk)
    if not request.POST:
        logger.error(f"api1_sumup_callback: expected POST, got {request.method}")
        return HttpResponse("Bad request", status=400, content_type="text/plain")

    '''
      {
        "id": "174f2e34-e7c5-40bb-b790-fa36e24d8631",
        "event_type": "solo.transaction.updated", # appears to be the only option with a reader
        "payload": {
          "client_transaction_id": "20bd747a-d5d2-4071-9099-abe7f56d1a42",
          "merchant_code": "M0JWH44Y",
          "status": "successful", # only other option seen sofar is 'failed'
          "transaction_id": "b5a3ccdf-e584-4da7-b760-6807dd1056ee"
        },
        "timestamp": "2025-09-25T18:24:42.606989Z"
      }
     '''
    try:
        data = json.loads(request.body)
        for f in ['id','event_type','payload','timestamp']:
           if not f in data or data[f] == None:
              raise Exception("Field f{f} missing from json")

        timestamp = dateutil.parser.isoparse(data['timestamp']

        payload = data['payload']
        for f in ['client_transaction_id','merchant_code','status','transaction_id']:
           if not f in payload or payload[f] == None:
               raise Exception("Field f{f} missing from json")
    except Exception as e:
        logger.error(f"api1_sumup_callback: json problem: f{e}\n\tf{request.body}")
        return HttpResponse("Bad request", status=400, content_type="text/plain")

    try:
       checkout = Checkout.objects.get(pk = sumup_pk)

    except Exception as e:
        logger.error(f"api1_sumup_callback could transact: {e}")
        return HttpResponse("Server error", status=500, content_type="text/plain")
