import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
    subject="Error in Pettycash credit",
):
    return
    admins = emails_for_group(settings.PETTYCASH_ADMIN_GROUP)
    if user and user.email:
        admins.append(user.email)
    else:
        if claim is not None and claim.src is not None and claim.src.email is not None:
            admins.append(claim.src.email)
    emailPlain(
        "pettycashclaims/email_fail.txt",
        toinform=admins,
        context={"error": error, "args": args, "claim": claim, "subject": subject},
    )


@login_required
def claims(request):
    claims = PettycreditClaim.objects.order_by("pk")
    out = []
    for c in claims:
        out.append(
            {"claim": c, "log": PettycreditClaimChange.objects.filter(claim_id=c)}
        )
    context = {
        "title": "Spend",
        "settings": settings,
        "claims": out,
    }
    return render(request, "pettycashclaims/claims.html", context)


@csrf_exempt
@is_paired_terminal
def api1_claim(request, terminal):
    p = {}
    for f in "uid", "amount", "desc":
        p[f] = request.POST.get(f)
        if not p[f]:
            logger.error(f"api1_claim: param {f} missing")
            return HttpResponse("Missing param", status=422, content_type="text/plain")
    hours = request.POST.get("hours")

    try:
        user = User.objects.get(pk=p["uid"])
    except User.DoesNotExist:
        logger.error(f"api1_claim: userid uid={p['uid']} not found")
        return HttpResponse("Not found", status=422, content_type="text/plain")

    claim = None
    try:
        p["amount"] = Money(float(p["amount"]), EUR)
        claim = PettycreditClaim(
            dst=User.objects.get(id=settings.POT_ID),
            src=user,
            description=f"[{terminal.name} claim]: {p['desc']}",
            amount=p["amount"],
        )
        if hours:
            claim.end_date = timezone.now() + timedelta(hours=float(hours))
        claim.save()
    except Exception as e:
        logger.error(f"api1_updateclaim: could complete claim: {e}")
        email_fail(
            subject="Error during creation of claim",
            user=user,
            error=e,
            terminal=terminal,
            claim=claim,
            args=p,
        )

        return HttpResponse("Error", status=500, content_type="text/plain")

    return HttpResponse(
        str(claim.pk).encode("ASCII"), status=200, content_type="text/plain"
    )


@csrf_exempt
@is_paired_terminal
def api1_updateclaim(request, terminal):
    p = {}
    for f in "cid", "desc":
        p[f] = request.POST.get(f)
        if not p[f]:
            logger.error(f"api1_claim: param {f} missing")
            return HttpResponse("Missing param", status=422, content_type="text/plain")
    hours = request.POST.get("hours")
    amount = request.POST.get("amount")

    p["desc"] = f"[{terminal.name} update]: {p['desc']}"
    try:
        if amount:
            amount = Money(float(amount), EUR)
        claim = PettycreditClaim.objects.get(pk=p["cid"])

        with transaction.atomic():
            PettycreditClaimChange(description=p["desc"], claim_id=claim).save()
            if amount:
                claim.amount = amount
            if hours:
                claim.end_date = timezone.now() + timedelta(hours=float(hours))
            if hours or amount:
                claim.save()
    except Exception as e:
        logger.error(f"api1_updateclaim: could complete updating claim: {e}")
        email_fail(
            subject="Error during update of claim",
            error=e,
            terminal=terminal,
            claim=claim,
            args=p,
        )
        return HttpResponse("Error", status=500, content_type="text/plain")

    return HttpResponse("OK", status=200, content_type="text/plain")


@csrf_exempt
@is_paired_terminal
def api1_settle(request, terminal):
    p = {}
    for f in "cid", "amount":
        p[f] = request.POST.get(f)
        if not p[f]:
            logger.error(f"api1_claim: param {f} missing")
            return HttpResponse("Missing param", status=422, content_type="text/plain")

    claim = None
    try:
        claim = PettycreditClaim.objects.get(pk=p["cid"])
        amount = Money(float(p["amount"]), EUR)
        desc = request.POST.get("desc")

        if not desc:
            desc = claim.desc

        claim.settle(f"[{terminal.name}] settle: {desc}", amount)
    except Exception as e:
        logger.error(f"api1_updateclaim: could settle claim: {e}")
        email_fail(
            subject="Error during settling of claim",
            error=e,
            terminal=terminal,
            claim=claim,
            args=p,
        )
        return HttpResponse("Error", status=500, content_type="text/plain")

    return HttpResponse("OK", status=200, content_type="text/plain")
