import json
import logging
from datetime import datetime, timedelta

import dateutil
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from moneyed import EUR, Money

from makerspaceleiden.mail import emailPlain, emails_for_group
from members.models import User
from terminal.decorators import is_paired_terminal

from .forms import CheckoutsForm
from .models import Checkout, gen_hash

logger = logging.getLogger(__name__)

# Max time of the actual unit is 60 seconds. But we've seen hours.
#
GRACE = timedelta(hours=100, minutes=0)


def email_fail(
    checkout=None,
    error="Unknown",
    args=None,
    subject="Error during SumUP paument",
):
    admins = emails_for_group(settings.PETTYCASH_ADMIN_GROUP)
    emailPlain(
        "sumup/email_fail.txt",
        toinform=admins,
        context={
            "error": error,
            "args": args,
            "subject": subject,
            "merchant": settings.SUMUP_MERCHANT,
            "demo": settings.SUMPUP_DEMO_MODE,
            "checkout": checkout,
        },
    )


@login_required
def index(request):
    filter = Q(state="SUCCESSFUL")

    if request.method == "POST":
        form = CheckoutsForm(request.POST)
        if form.is_valid():
            f = form.cleaned_data
            print(f)
            if f["state"] == "1":
                filter = Q(state="SUCCESSFUL") | Q(state="SUBMITTED")
            elif f["state"] == "2":
                filter = Q()
            if f["from_date"]:
                filter &= Q(date__gte=f["from_date"])
            if f["until_date"]:
                filter &= Q(date__lte=f["until_date"])
            if f["user"]:
                filter &= Q(member=f["user"])
    else:
        form = CheckoutsForm()
    print(filter)

    context = {
        "form": form,
        "title": "Recent SumUP transactions",
        "checkout_items": Checkout.objects.all().filter(filter).order_by("-date"),
        "merchant": settings.SUMUP_MERCHANT,
        "demo": settings.SUMPUP_DEMO_MODE,
    }
    return render(request, "sumup/index.html", context)


@csrf_exempt
@is_paired_terminal
def api1_sumup_pay(request, terminal):
    if terminal.pk not in settings.SUMUP_TERMINALS:
        logger.error(
            f"api1_sumup_pay: payment request from terminal {terminal}, #{terminal.pk} which is not in the list of SUMUP_TERMINALs"
        )
        return HttpResponse("Bad request", status=400, content_type="text/plain")

    if request.method != "POST":
        logger.error("api1_sumup_pay: expected POST")
        return HttpResponse("Bad request", status=400, content_type="text/plain")

    p = {}
    for f in ["userid", "amount"]:
        if f not in request.POST or len(request.POST.getlist(f)) != 1:
            logger.error(f"api1_sumup_pay: param {f} missing/not singular")
            return HttpResponse("Missing param", status=422, content_type="text/plain")
        p[f] = "".join(request.POST.getlist(f))

    try:
        member = User.objects.get(pk=p["userid"])
        amount = Money(float(p["amount"]), EUR)
    except Exception as e:
        logger.error(f"api1_sumup_pay could process data {p} : {e}")
        return HttpResponse("Missing param", status=422, content_type="text/plain")

    try:
        checkout = Checkout(member=member, amount=amount, terminal=terminal)
        checkout.transact()
    except Exception as e:
        logger.error(f"api1_sumup_pay not could transact: {e}")
        return HttpResponse("Server error", status=500, content_type="text/plain")

    return HttpResponse("OK")


@csrf_exempt
def api1_sumup_callback(request, sumup_pk, timeint, hash):
    if request.method != "POST":
        logger.error(f"api1_sumup_callback: expected POST, got {request.method}")
        return HttpResponse("Bad request", status=400, content_type="text/plain")

    if gen_hash(sumup_pk, timeint) != hash:
        logger.error("api1_sumup_callback: wrong hash")
        return HttpResponse("Ignored", status=200, content_type="text/plain")

    f = (datetime.now() - GRACE).timestamp()
    t = datetime.now().timestamp()
    if timeint < f or timeint > t:
        logger.error(f"api1_sumup_callback: time {timeint} outside range {f}..{t}")
        # return HttpResponse("Bad request", status=400, content_type="text/plain")

    logger.debug(request.body)
    try:
        data = json.loads(request.body)
        for f in ["id", "event_type", "payload", "timestamp"]:
            if f not in data:
                raise Exception("Field {f} missing from json")

        timestamp = dateutil.parser.isoparse(data["timestamp"])

        payload = data["payload"]
        for f in ["client_transaction_id", "merchant_code", "status", "transaction_id"]:
            if f not in payload:
                raise Exception(f"Field f{f} missing from json")

    except Exception as e:
        logger.error(f"api1_sumup_callback: json problem: f{e}\n\tf{request.body}")
        email_fail(
            None, "Error while parsing Sumup response. No deposit.", request.body
        )
        return HttpResponse("Bad request", status=400, content_type="text/plain")

    try:
        checkout = Checkout.objects.get(pk=sumup_pk)
        checkout.debug_note = data
        checkout.transaction_date = timestamp
        checkout.status = "ERROR"

        if (
            data["event_type"] == "solo.transaction.updated"
            and payload["merchant_code"] == settings.SUMUP_MERCHANT
            and checkout.client_transaction_id == payload["client_transaction_id"]
            and payload["status"] in ["successful", "failed"]
        ):
            checkout.status = "FAILED"

        if payload["status"] == "successful":
            checkout.deposit(payload["transaction_id"], timestamp)
        else:
            checkout.state = "CANCELLED"
            checkout._change_reason = "Valid callback, with status set to failed - generally a user that cancelled or a timeout on the SOLO"
            logger.error(
                "api1_sumup_callback: report of failed from cb, user propably canceled."
            )
            checkout.save()

        # No email on failed - is 'normal'
        return HttpResponse("OK", status=200, content_type="text/plain")

        logger.error(f"api1_sumup_callback: failed to process: {request.body}")
        checkout.debug_note = data
        checkout._change_reason = (
            "Valid callback, but the data could not be recignized."
        )
        checkout.save()

        email_fail(
            checkout, "Sumup response could not be processed. No deposit.", request.body
        )

    except Exception as e:
        logger.error(f"api1_sumup_callback could not transact: e={e}")
        checkout._change_reason = "Valid callback, but exception while handling it"
        checkout.debug_note = {"err": "exception", "data": data, "erm": e}
        if checkout:
            try:
                checkout.save()
            except Exception as e:
                pass
        email_fail(
            checkout, "Error while processing Sumup response. No deposit.", request.body
        )

    # We may need to make this a 200 -- as to quell needless retries.
    return HttpResponse("Server error", status=500, content_type="text/plain")
