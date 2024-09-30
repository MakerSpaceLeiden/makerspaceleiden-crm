import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from makerspaceleiden.decorators import superuser_required
from makerspaceleiden.mail import emailPlain
from makerspaceleiden.utils import client_cert, client_ip, server_cert
from members.models import Tag, User
from pettycash.models import PettycashStation
from terminal.decorators import is_paired_terminal

from .models import Terminal, terminal_admin_emails

logger = logging.getLogger(__name__)


@superuser_required
def forget(request, pk):
    try:
        tx = Terminal.objects.get(id=pk)
        tx.delete()
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")
    except Exception:
        logger.error("Delete failed")

    return redirect("unpaired")


@csrf_exempt
def api_none(request):
    # Very short reply - for CA_fetch/tests by IoT hardware with
    # limited heap/memory.
    return HttpResponse("OK\n", status=200, content_type="text/plain")


def _register(request):
    ip = client_ip(request)
    if ip is None:
        logger.error("Bad request,IP  sender unclear")
        return HttpResponse(
            "No client address, rejecting", status=400, content_type="text/plain"
        )

    client_sha = client_cert(request)
    server_sha = server_cert(request)

    if client_sha is None or server_sha is None:
        return HttpResponse(
            "No identifier, rejecting", status=400, content_type="text/plain"
        )

    # 2. If we do not yet now this cert - add its fingrerprint to the database
    #    and mark it as pending. Return a secret/nonce.
    #
    try:
        terminal = Terminal.objects.get(fingerprint=client_sha)

    except ObjectDoesNotExist:
        logger.info(
            "Fingerprint %s not found, adding to the list of unknowns" % client_sha
        )

        name = request.GET.get("name", None)
        if not name:
            logger.error(
                "Bad request, client unknown, no name provided (%s @ %s"
                % (client_sha, ip)
            )
            return HttpResponse(
                "Bad request, missing name", status=400, content_type="text/plain"
            )

        terminal = Terminal(fingerprint=client_sha, name=name, accepted=False)
        terminal.nonce = secrets.token_hex(32)
        terminal.accepted = False
        reason = "Added on first contact; from IP address %s" % (ip)
        terminal._change_reason = reason[:100]
        terminal.save()

        logger.info("Issuing first time nonce to %s at %s" % (client_sha, ip))
        return HttpResponse(terminal.nonce, status=401, content_type="text/plain")

    # 3. If this is a new terminal; check that it has the right nonce from the initial
    #    exchange; and verify that it knows a secret (the tag id of an admin). If so
    #    auto approve it.
    #
    if terminal.accepted:
        return terminal

    cutoff = timezone.now() - timedelta(minutes=settings.PAY_MAXNONCE_AGE_MINUTES)
    if cutoff > terminal.date:
        logger.info("Fingerprint %s known, but too old. Issuing new one." % client_sha)
        terminal.nonce = secrets.token_hex(32)
        terminal.date = timezone.now()
        terminal._change_reason = (
            "Updating nonce, repeat register; but the old one was too old."
        )
        terminal.save()
        logger.info("Updating nonce for  %s at %s" % (client_sha, ip))
        return HttpResponse(terminal.nonce, status=401, content_type="text/plain")

    response = request.GET.get("response", None)
    if not response:
        logger.error(
            "Bad request, missing response for known %s at %s" % (client_sha, ip)
        )
        return HttpResponse(
            "Bad request, missing response", status=400, content_type="text/plain"
        )

    # This response should be the SHA256 of nonce + tag + client-cert-sha256 + server-cert-256.
    # and the tag should be owned by someone whcih has the right admin rights.
    #
    for tag in Tag.objects.all().filter(
        owner__groups__name=settings.PETTYCASH_ADMIN_GROUP
    ):
        m = hashlib.sha256()
        m.update(terminal.nonce.encode("ascii"))
        m.update(tag.tag.encode("ascii"))
        m.update(bytes.fromhex(client_sha))
        m.update(bytes.fromhex(server_sha))
        sha = m.hexdigest()

        if sha.lower() == response.lower():
            terminal.accepted = True
            reason = "%s, IP=%s tag-=%d %s" % (
                terminal.name,
                ip,
                tag.id,
                tag.owner,
            )
            terminal._change_reason = reason[:100]
            terminal.save()
            logger.error(
                "Terminal %s accepted, tag swipe by %s matched." % (terminal, tag.owner)
            )

            emailPlain(
                "email_accept.txt",
                toinform=terminal_admin_emails(),
                context={
                    "base": settings.BASE,
                    "settings": settings,
                    "tag": tag,
                    "terminal": terminal,
                },
            )

            # proof to the terminal that we know the tag too. This prolly
            # should be an HMAC
            #
            m = hashlib.sha256()
            m.update(tag.tag.encode("ascii"))
            m.update(bytes.fromhex(sha))
            sha = m.hexdigest()
            return HttpResponse(sha, status=200, content_type="text/plain")

    logger.error(
        "RQ ok; but response could not be correlated to a tag (%s, ip=%s, c=%s)"
        % (terminal, ip, client_sha)
    )
    return HttpResponse("Accepting failed", status=400, content_type="text/plain")


@csrf_exempt
def api3_register(request):
    result = _register(request)

    if isinstance(result, HttpResponse):
        return result

    return HttpResponse("Found", status=302, content_type="text/plain")


@csrf_exempt
def api2_register(request):
    result = _register(request)
    if isinstance(result, HttpResponse):
        return result

    if not isinstance(result, Terminal):
        return HttpResponse("Internal Error", status=500, content_type="text/plain")

    terminal = result

    # We're talking to an approved terminal - give it its SKU list if it has
    # been wired to a station; or just an empty list if we do not know yet.
    #
    try:
        station = PettycashStation.objects.get(terminal=terminal.id)
    except ObjectDoesNotExist:
        return JsonResponse({})

    avail = []
    for item in station.available_skus.all():
        e = {
            "name": item.name,
            "description": item.description,
            "price": item.amount.amount,
        }
        if item == station.default_sku:
            e["default"] = True
        avail.append(e)

    return JsonResponse(
        {
            "name": terminal.name,
            "description": station.description,
            "pricelist": avail,
        },
        safe=False,
    )


@csrf_exempt
@is_paired_terminal
def api3_notify(request, terminal):
    p = {}
    for f in "from", "to", "subject", "msg":
        p[f] = request.POST.getlist(f)
        if not p[f]:
            logger.error(f"api3_notify: param {f} missing")
            return HttpResponse("Missing param", status=422, content_type="text/plain")

    sender = None
    if p["from"][0] != terminal.name:
        try:
            sender = User.objects.get(pk=p["from"][0])
        except Exception:  # also catch invalid conversions, etc.
            logger.error(f"api3_notify: user {p['from']} not found")
            return HttpResponse("Not found", status=404, content_type="text/plain")

    dests = []
    for to in p["to"]:
        if to in settings.NOTIFICATION_MAP:
            # Allow the entry to be empty - as to effectively
            # filter things (useful; as firmware is harder to change).
            #
            if settings.NOTIFICATION_MAP[to]:
                dests.append(settings.NOTIFICATION_MAP[to])
            continue

        try:
            g = (
                User.objects.all()
                .filter(groups__name=to)
                .values_list("email", flat=True)
            )
            if g:
                dests.append(g)
                continue

            d = User.objects.get(pk=to)
            dests.append(d.email)
        except Exception:
            logger.error(f"api3_notify: dest {to} not found")

    if not dests:
        logger.error(f"api3_notify: no destinations at all for <{p['to']}>, givign up.")
        return HttpResponse("Not found", status=404, content_type="text/plain")

    emailPlain(
        "node_notify.txt",
        subject=f"[{terminal.name}] {p['subject'][0]}",
        toinform=dests,
        context={
            "terminal": terminal,
            "subject": p["subject"][0],
            "msg": p["msg"][0],
            "to": p["to"],
            "sender": sender,
        },
    )
    return HttpResponse("Sent", status=200, content_type="text/plain")
