import logging
from datetime import date, datetime
from email.mime.image import MIMEImage

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.forms import widgets
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from moneyed import EUR, Money
from moneyed.l10n import format_money

from makerspaceleiden.decorators import (
    login_or_priveleged,
    superuser_or_bearer_required,
    superuser_required,
)
from makerspaceleiden.mail import emailPlain
from members.models import Tag, User
from terminal.decorators import is_paired_terminal
from terminal.models import Terminal
from terminal.views import api2_register as new_api2_register

from .camt53 import camt53_process
from .forms import (
    CamtUploadForm,
    ImportProcessForm,
    PettycashDeleteForm,
    PettycashPairForm,
    PettycashPayoutRequestForm,
    PettycashReimburseHandleForm,
    PettycashReimbursementRequestForm,
    PettycashTransactionForm,
)
from .models import (
    PettycashBalanceCache,
    PettycashImportRecord,
    PettycashReimbursementRequest,
    PettycashSku,
    PettycashStation,
    PettycashTransaction,
    pettycash_admin_emails,
)

logger = logging.getLogger(__name__)


def mtostr(m):
    return format_money(m, locale="nl_NL")


def client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def image2mime(img):
    ext = img.name.split(".")[-1]
    name = img.name.split("/")[-1]
    attachment = MIMEImage(img.read(), ext)
    attachment.add_header("Content-Disposition", 'inline; filename="' + name + '"')
    return attachment


def pettycash_treasurer_emails():
    return pettycash_admin_emails()


# Note - we do this here; rather than in the model its save() - as this
# lets admins change things through the database interface silently.
# Which can help when sheparding the community.
#
def alertOwnersToChange(
    tx, userThatMadeTheChange=None, toinform=[], reason=None, template="email_tx.txt"
):
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

    if userThatMadeTheChange.email not in toinform:
        toinform.append(userThatMadeTheChange.email)

    # if settings.ALSO_INFORM_EMAIL_ADDRESSES:
    #    toinform.extend(settings.ALSO_INFORM_EMAIL_ADDRESSES)

    return emailPlain(
        template,
        toinform=toinform,
        context={
            "user": userThatMadeTheChange,
            "base": settings.BASE,
            "reason": reason,
            "tx": tx,
            "src_label": src_label,
            "dst_label": dst_label,
            "label": label,
            "settings": settings,
        },
    )


def pettycash_redirect(pk=None):
    url = reverse("mytransactions")
    if pk:
        url = "{}#{}".format(url, pk)
    return redirect(url)


def transact_raw(
    request,
    src=None,
    dst=None,
    description=None,
    amount=None,
    reason=None,
    user=None,
    sent_alert=True,
):
    if None in [src, dst, description, amount, reason, user]:
        logger.error("Transact raw called with missing arguments. bug.")
        return 0

    try:
        tx = PettycashTransaction(
            src=src, dst=dst, description=description, amount=amount
        )
        logger.info("payment: %s" % reason)
        tx._change_reason = reason[:100]
        priv = False
        if request.user.is_authenticated:
            priv = request.user.is_privileged
        tx.save(is_privileged=priv)
        if sent_alert:
            alertOwnersToChange(tx, user, [])

    except Exception as e:
        logger.error(
            "Unexpected error during initial (raw) save of new pettycash: {}".format(e)
        )
        return 0

    return 1


def transact(
    request, label, src=None, dst=None, description=None, amount=None, reason=None
):
    form = PettycashTransactionForm(
        request.POST or None,
        initial={"src": src, "dst": dst, "description": description, "amount": amount},
        is_privileged=request.user.is_privileged,
    )
    if form.is_valid():
        item = form.save(commit=False)

        if item.amount < Money(0, EUR) or item.amount > settings.MAX_PAY_CRM:
            if not request.user.is_privileged:
                return HttpResponse(
                    "Only transactions between %s and %s"
                    % (Money(0, EUR), settings.MAX_PAY_CRM),
                    status=406,
                    content_type="text/plain",
                )
            logger.info(
                "Allowing super user perms to do a non compliant transaction %s"
                % (item)
            )

        if not item.description:
            item.description = "Entered by {}".format(request.user)

        if transact_raw(
            request,
            src=item.src,
            dst=item.dst,
            description=item.description,
            amount=item.amount,
            reason="Logged in as {}, {}.".format(request.user, reason),
            user=request.user,
        ):
            return pettycash_redirect(item.id)

        return HttpResponse(
            "Something went wrong ??", status=500, content_type="text/plain"
        )

    if src:
        form.fields["src"].widget = widgets.HiddenInput()
    if dst:
        form.fields["dst"].widget = widgets.HiddenInput()

    products = None
    if dst == settings.POT_ID:
        products = PettycashSku.objects.all().order_by("name")

    context = {
        "title": label,
        "form": form,
        "action": "Pay",
        "products": products,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "pettycash/invoice.html", context)


@login_required
def index(request, days=30):
    lst = (
        PettycashBalanceCache.objects.all()
        .filter(~Q(owner=settings.NONE_ID))
        .order_by("-lasttxdate")
    )
    prices = PettycashSku.objects.all()
    context = {
        "title": "Balances",
        "lst": lst,
        "settings": settings,
        "pricelist": prices,
        "has_permission": request.user.is_authenticated,
        "user": request.user,
        "last_import": PettycashImportRecord.objects.all().last(),
    }
    return render(request, "pettycash/index.html", context)


@login_required
def pricelist(request, days=30):
    prices = PettycashSku.objects.all().order_by("name")

    context = {
        "title": "Pricelist",
        "settings": settings,
        "has_permission": request.user.is_authenticated,
        "pricelist": prices,
    }
    return render(request, "pettycash/pricelist.html", context)


@login_required
def spends(request):
    skus = PettycashSku.objects.order_by("name")
    per_sku = []
    frst = timezone.now()
    for sku in skus:
        e = {
            "name": sku.name,
            "sku": sku,
            "description": sku.description,
            "amount": Money(0, EUR),
            "count": 0,
            "price": sku.amount,
        }
        desc = sku.name
        if sku.description:
            desc = sku.description
        for tx in PettycashTransaction.objects.all().filter(
            description__startswith=desc
        ):
            e["amount"] += tx.amount
            e["count"] += 1
            if frst > tx.date:
                frst = tx.date
        per_sku.append(e)
    context = {
        "title": "Spend",
        "settings": settings,
        "has_permission": request.user.is_authenticated,
        "per_sku": per_sku,
        "skus": skus,
        "first": frst,
        "delta": timezone.now() - frst,
    }
    return render(request, "pettycash/spend.html", context)


@login_required
def qrcode(request):
    description = request.GET.get("description", None)
    amount_str = request.GET.get("amount", 0)
    # LR: A bit ugly but money will produce amounts with a comma.
    amount_str = amount_str.replace(",", ".")
    amount = Money(amount_str, EUR)

    context = {
        "title": "QR code",
        "description": description,
        "amount": amount,
        "has_permission": request.user.is_authenticated,
        "url": "%s?description=%s&amount=%s"
        % (request.build_absolute_uri("/pettycash/pay"), description, amount_str),
    }
    return render(request, "pettycash/qrcode.html", context)


@login_required
@login_or_priveleged
def invoice(request, src):
    try:
        src = User.objects.get(id=src)
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")

    return transact(
        request,
        "%s to pay to %s " % (src, settings.POT_LABEL),
        src=src,
        dst=settings.POT_ID,
        reason="Invoice via website",
    )


@login_required
@login_or_priveleged
def transfer_to_member(request, src):
    src = request.user
    description = "Transfer"
    amount = Money(0, EUR)
    form = PettycashTransactionForm(
        request.POST or None,
        initial={"src": src, "description": description, "amount": amount},
        is_privileged=request.user.is_privileged,
    )

    if form.is_valid():
        reason = "Transfer"
        item = form.save(commit=False)
        if not item.dst:
            item.dst = User.objects.get(id=settings.POT_ID)
        if not transact_raw(
            request,
            src=request.user,
            dst=item.dst,
            description=item.description,
            amount=item.amount,
            reason="Logged in as {}, {}.".format(request.user, reason),
            user=request.user,
        ):
            return HttpResponse(
                "Transaction failed", status=500, content_type="text/plain"
            )
        return pettycash_redirect(item.id)

    if src:
        form.fields["src"].widget = widgets.HiddenInput()

    context = {
        "form": form,
        "has_permission": request.user.is_authenticated,
    }

    return render(request, "pettycash/transfer_to_member.html", context)


@login_required
@login_or_priveleged
def transfer(request, src, dst):
    try:
        src = User.objects.get(id=src)
        dst = User.objects.get(id=dst)
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")

    dst_label = dst
    if dst.id == settings.POT_ID:
        dst_label = settings.POT_LABEL

    return transact(
        request,
        "%s to pay %s" % (src, dst_label),
        src=src,
        dst=dst,
        reason="Transfer form website",
    )


@login_required
def unpaired(request):
    lst = (
        Terminal.objects.all()
        .filter(Q(accepted=True) & Q(station=None))
        .order_by("-date")
    )
    unlst = Terminal.objects.all().filter(Q(accepted=False))
    paired = PettycashStation.objects.all().filter(~Q(terminal=None))
    unpaired = PettycashStation.objects.all().filter(Q(terminal=None))
    context = {
        "title": "Assigning terminal",
        "has_permission": request.user.is_authenticated,
        "lst": lst,
        "unlst": unlst,
        "paired": paired,
        "unpaired": unpaired,
        "settings": settings,
    }
    return render(request, "pettycash/unpaired.html", context)


@superuser_required
def cam53upload(request):
    if request.method == "POST":
        form = CamtUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES["cam53file"]
                print(file)
                txs = camt53_process(file)

                valids = any(d["success"] for d in txs)

                ids = []
                for tx in txs:
                    if tx["success"]:
                        ids.append(
                            {
                                "description": tx["description"],
                                "user": tx["user"],
                                "amount": tx["amount"],
                                "change_reason": "TXREF=%s, %s IBAN=%s"
                                % (
                                    tx["ref"],
                                    tx["name_str"],
                                    tx["iban_str"],
                                ),
                            }
                        )

                okf = ImportProcessForm(ids)  # list(map(lambda x: x['id'], txs)))

                context = {
                    "title": "Import log",
                    "has_permission": request.user.is_authenticated,
                    "settings": settings,
                    "txs": txs,
                    "valids": valids,
                    "form": okf,
                    "action": "Deposit for real",
                }
                return render(request, "pettycash/importlog.html", context)

            except Exception as e:
                return HttpResponse(
                    "FAIL: %s" % e, status=500, content_type="text/plain"
                )

            # Redirect to the document list after POST
            return HttpResponse("Unknown FAIL", status=500, content_type="text/plain")
    else:
        form = CamtUploadForm()  # A empty, unbound form

    context = {
        "title": "Upload CAM53 transactions",
        "has_permission": request.user.is_authenticated,
        "settings": settings,
        "form": form,
        "action": "upload",
    }
    return render(request, "pettycash/upload.html", context)


@superuser_required
def cam53process(request):
    if request.method != "POST":
        return HttpResponse("Unknown FAIL", status=400, content_type="text/plain")

    #    reason = CsrfViewMiddleware().process_view(request, None, (), {})
    #    if reason:
    ##        return HttpResponse("CSRF FAIL", status=400, content_type="text/plain")

    ok = []
    failed = []
    skipped = []
    vals = request.POST.dict()
    for i in range(int(vals["vals"])):
        try:
            if vals.get("ok_%d" % i, "off") == "on":
                user = User.objects.get(id=vals["user_%d" % i])
                amount = Money(vals["amount_%d" % i], EUR)
                tx = PettycashTransaction(
                    src=User.objects.get(id=settings.POT_ID), dst=user, amount=amount
                )
                tx.description = vals["description_%d" % i]
                tx._change_reason = vals["change_reason_%d" % i][:100]
                tx.save()
                alertOwnersToChange(
                    tx,
                    request.user,
                    [tx.src.email, tx.dst.email],
                    "Banking transaction processed; %s deposited" % tx.amount,
                    "deposit_tx.txt",
                )
                ok.append(tx)
            else:
                skipped.append(
                    "%s: %s"
                    % (
                        vals.get("description_%d" % i, "??"),
                        vals.get("amount_%d" % i, "??"),
                    )
                )
        except Exception as e:
            failed.append(
                "%d: %s %s: %s<br>%s"
                % (
                    i,
                    vals.get("change_reason_%d" % i, "??"),
                    vals.get("description_%d" % i, "??"),
                    vals.get("amount_%d" % i, "??"),
                    e,
                )
            )
    if ok:
        try:
            record = PettycashImportRecord.objects.create(by=request.user)
            record.save()
        except Exception:
            logger.error("Had issues recording transaction import")

    context = {
        "title": "Import Results",
        "settings": settings,
        "ok": ok,
        "failed": failed,
        "skipped": skipped,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "pettycash/importlog-results.html", context)


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


@superuser_required
def pair(request, pk):
    try:
        tx = Terminal.objects.get(id=pk)
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")

    form = PettycashPairForm(request.POST or None)
    if form.is_valid():
        station = form.cleaned_data["station"]
        reason = "%s (by %s)" % (
            form.cleaned_data["reason"],
            request.user,
        )

        tx.accepted = True
        tx._change_reason = reason[:100]
        tx.save()

        station.terminal = tx
        station._change_reason = reason[:100]
        station.save()

        return redirect("unpaired")

    context = {
        "title": "Pair %s" % (tx.name),
        "tx": tx,
        "settings": settings,
        "form": form,
        "user": request.user,
        "action": "pair",
        "has_permission": request.user.is_authenticated,
    }

    return render(request, "pettycash/pair.html", context)


@csrf_exempt
def api_none(request):
    # Very short reply - for CA_fetch/tests by IoT hardware with
    # limited heap/memory.
    return HttpResponse("OK\n", status=200, content_type="text/plain")


@superuser_required
def deposit(request, dst):
    try:
        dst = User.objects.get(id=dst)
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")

    dst_label = dst
    if dst.id == settings.POT_ID:
        dst_label = settings.POT_LABEL

    return transact(
        request,
        "Deposit into account %s" % (dst_label),
        dst=dst,
        src=settings.POT_ID,
        reason="Deposit via website",
        description="Deposit",
    )


@login_required
def showtx(request, pk):
    try:
        tx = PettycashTransaction.objects.get(id=pk)
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")

    context = {
        "title": "Details transaction %s @ %s" % (tx.id, tx.date),
        "tx": tx,
        "settings": settings,
        "has_permission": request.user.is_authenticated,
    }

    return render(request, "pettycash/details.html", context)


@login_required
def show_mine(request):
    user = request.user
    balance = 0
    lst = []

    try:
        balance = PettycashBalanceCache.objects.get(owner=user)
        lst = (
            PettycashTransaction.objects.all()
            .filter(Q(src=user) | Q(dst=user))
            .order_by("date")
        )
    except ObjectDoesNotExist:
        pass

    context = {
        "title": "SpaceTegoed",
        "balance": balance,
        "who": user,
        "lst": lst,
        "queue": PettycashReimbursementRequest.objects.all().count(),
        "has_permission": request.user.is_authenticated,
        "admins": User.objects.all()
        .filter(groups__name=settings.PETTYCASH_ADMIN_GROUP)
        .order_by("last_name"),
        "last_import": PettycashImportRecord.objects.all().last(),
    }

    return render(request, "pettycash/view_mine.html", context)


@login_required
def manual_deposit(request):
    topup = settings.PETTYCASH_TOPUP
    try:
        balance = PettycashBalanceCache.objects.get(owner=request.user)
        topup = (
            int((-float(balance.balance.amount) + settings.PETTYCASH_TOPUP) / 5 + 0.5)
            * 5
        )
    except ObjectDoesNotExist:
        pass

    context = {
        "title": "Perform a manual deposit",
        "settings": settings,
        "user": request.user,
        "has_permission": request.user.is_authenticated,
        # String according to Quick Response Code richtlijnen van de Europese Betalingsraad (EPC).
        # See: https://epc-qr.eu. We need to do this here; rather than in the template; as the
        # latter does not allow for for line breaks (qr_from_text).
        #
        "epc": "BCD\n002\n1\nSCT\n\n%s\n%s\nEUR%.2f\n\n\nStorting Spacepot %s / %s\n"
        % (
            settings.PETTYCASH_TNS,
            settings.PETTYCASH_IBAN,
            topup,
            request.user.pk,
            request.user,
        ),
    }

    return render(request, "pettycash/manual_deposit.html", context)


@login_required
def showall(request):
    balance = 0
    lst = []
    try:
        lst = PettycashTransaction.objects.all().order_by("date")
    except ObjectDoesNotExist:
        pass

    for tx in lst:
        balance += tx.amount

    context = {
        "title": "All transactions",
        "has_permission": request.user.is_authenticated,
        "lst": lst,
        "balance": balance,
    }

    return render(request, "pettycash/alldetails.html", context)


@login_required
def show(request, pk):
    try:
        user = User.objects.get(id=pk)
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")
    balance = None
    lst = []
    moneys_in = 0  # Money(0,EUR)
    moneys_out = 0  # Money(0,EUR)
    try:
        balance = PettycashBalanceCache.objects.get(owner=user)
        lst = (
            PettycashTransaction.objects.all()
            .filter(Q(src=user) | Q(dst=user))
            .order_by("date")
        )
        for tx in lst:
            if tx.dst == user:
                moneys_in += tx.amount
            else:
                moneys_out += tx.amount
    except ObjectDoesNotExist:
        pass

    label = user
    if user.id == settings.POT_ID:
        label = settings.POT_LABEL

    context = {
        "title": "Balance and transactions for %s" % (label),
        "has_permission": request.user.is_authenticated,
        "balance": balance,
        "who": user,
        "lst": lst,
        "in": moneys_in,
        "out": moneys_out,
    }

    return render(request, "pettycash/view.html", context)


@login_required
def pay(request):
    amount_str = request.GET.get("amount", None)
    # LR: A bit ugly but money will produce amounts with a comma.
    amount_str = amount_str.replace(",", ".")
    description = request.GET.get("description", None)

    if not amount_str and not description:
        return HttpResponse(
            "Amount/Description parameters mandatory",
            status=400,
            content_type="text/plain",
        )
    amount = Money(amount_str, EUR)

    return transact(
        request,
        "%s wants to pay %s to the Makerspace for %s"
        % (request.user, mtostr(amount), description),
        src=request.user,
        dst=settings.POT_ID,
        amount=amount,
        description=description,
        reason="Pay via website",
    )


@login_required
def delete(request, pk):
    try:
        tx = PettycashTransaction.objects.get(id=pk)
    except ObjectDoesNotExist:
        return HttpResponse("Not found", status=404, content_type="text/plain")

    if (
        request.user != tx.src
        and request.user != tx.dst
        and not request.user.is_privileged
    ):
        return HttpResponse(
            "Not allowed (you can only delete your own payments.",
            status=404,
            content_type="text/plain",
        )

    form = PettycashDeleteForm(request.POST or None)
    if form.is_valid():
        reason = "%s (by %s)" % (form.cleaned_data["reason"], request.user)
        tx._change_reason = reason[:100]
        # tx.delete();
        tx.refund_booking()
        alertOwnersToChange(
            tx, request.user, [tx.src.email, tx.dst.email], reason, "delete_tx.txt"
        )
        return redirect("transactions", pk=request.user.id)

    context = {
        "title": "Delete transaction %s @ %s" % (tx.id, tx.date),
        "has_permission": request.user.is_authenticated,
        "tx": tx,
        "settings": settings,
        "form": form,
        "user": request.user,
        "action": "delete",
    }

    return render(request, "pettycash/delete.html", context)


@login_required
def payoutform(request):
    form = PettycashPayoutRequestForm(
        request.POST or None,
        request.FILES or None,
        initial={
            "src": request.user,
            "dst": User.objects.get(id=settings.POT_ID),
            "date": date.today(),
        },
        is_privileged=request.user.is_privileged,
    )
    context = {
        "settings": settings,
        "form": form,
        "label": "Payout",
        "action": "request",
        "user": request.user,
        "has_permission": request.user.is_authenticated,
        "is_privileged": request.user.is_privileged,
    }

    if form.is_valid():
        item = form.save(commit=False)
        item.dst = User.objects.get(id=settings.POT_ID)
        item.viaTheBank = True
        item.isPayout = True
        if not item.date:
            item.date = datetime.now()
        if not item.submitted:
            item.submitted = datetime.now()

        item.save()
        context["item"] = item

        emailPlain(
            "email_payout_notify.txt",
            toinform=[pettycash_treasurer_emails(), request.user.email],
            context=context,
        )
        return render(request, "pettycash/reimburse_ok.html", context=context)
    return render(request, "pettycash/reimburse_form.html", context=context)


@login_required
def reimburseform(request):
    form = PettycashReimbursementRequestForm(
        request.POST or None,
        request.FILES or None,
        initial={
            "src": User.objects.get(id=settings.POT_ID),
            "dst": request.user,
            "date": date.today(),
        },
        is_privileged=request.user.is_privileged,
    )
    context = {
        "settings": settings,
        "form": form,
        "label": "Reimburse",
        "action": "request",
        "user": request.user,
        "has_permission": request.user.is_authenticated,
    }

    if form.is_valid():
        item = form.save(commit=False)
        if not item.date:
            item.date = datetime.now()
        if not item.submitted:
            item.submitted = datetime.now()
        item.src = User.objects.get(id=settings.POT_ID)

        item.save()
        context["item"] = item

        attachments = []
        if item.scan:
            attachments.append(image2mime(item.scan))

        emailPlain(
            "email_imbursement_notify.txt",
            toinform=[pettycash_treasurer_emails(), request.user.email],
            context=context,
            attachments=attachments,
        )

        return render(request, "pettycash/reimburse_ok.html", context=context)

    return render(request, "pettycash/reimburse_form.html", context=context)


@login_required
def reimburseque(request):
    if not request.user.is_anonymous and request.user.can_escalate_to_priveleged:
        if not request.user.is_privileged:
            return redirect("sudo")
    if not request.user.is_privileged:
        return HttpResponse("XS denied", status=401, content_type="text/plain")

    if not request.user.groups.filter(name=settings.PETTYCASH_TREASURER_GROUP).exists():
        return HttpResponse("XS denied", status=401, content_type="text/plain")

    context = {
        "settings": settings,
        "label": "Reimburse",
        "action": "request",
        "user": request.user,
        "has_permission": request.user.is_authenticated,
    }
    form = PettycashReimburseHandleForm(request.POST or None)
    if form.is_valid():
        pk = form.cleaned_data["pk"]
        reason = form.cleaned_data["reason"].rstrip()
        if reason:
            reason = reason + "\n"

        approved = False
        if "approved" in (request.POST["submit"]):
            approved = True
        try:
            item = PettycashReimbursementRequest.objects.get(id=pk)
            context["item"] = item
            context["approved"] = approved
            context["reason"] = reason

            attachments = []
            if item.scan:
                attachments.append(image2mime(item.scan))

            if approved:
                context["reason"] = "Approved by %s (%d)" % (request.user, item.pk)
                if item.viaTheBank:
                    emailPlain(
                        "email_imbursement_bank_approved.txt",
                        toinform=[pettycash_treasurer_emails(), request.user.email],
                        context=context,
                        attachments=attachments,
                    )
                if item.isPayout or not item.viaTheBank:
                    if item.viaTheBank:
                        emailPlain(
                            "email_payout_bank_approved.txt",
                            toinform=[pettycash_treasurer_emails(), request.user.email],
                            context=context,
                            attachments=attachments,
                        )
                    if not transact_raw(
                        request,
                        src=item.src,
                        dst=item.dst,
                        description=item.description,
                        amount=item.amount,
                        reason=context["reason"],
                        user=request.user,
                        sent_alert=False,
                    ):
                        logger.error(
                            "Transaction failed. Queued item %s Not deleted from the queuue."
                            % (item.pk)
                        )
                        return HttpResponse(
                            "Failure", status=500, content_type="text/plain"
                        )

            else:
                context["reason"] = "Rejected by %s (%d)" % (request.user, item.pk)
                emailPlain(
                    "email_imbursement_rejected.txt",
                    toinform=[pettycash_treasurer_emails(), request.user.email],
                    context=context,
                    attachments=attachments,
                )

            item._change_reason = context["reason"]
            item.delete()

            return redirect(reverse("reimburse_queue"))

        except ObjectDoesNotExist:
            logger.error("Reimbursment %d not found" % (pk))
            return HttpResponse(
                "Reimbursement not found", status=404, content_type="text/plain"
            )

    items = []
    for tx in PettycashReimbursementRequest.objects.all().order_by("submitted"):
        item = {}
        item["tx"] = tx
        item["form"] = PettycashReimburseHandleForm(initial={"pk": tx.pk})
        item["action"] = "foo"
        items.append(item)

    context["items"] = items
    return render(request, "pettycash/reimburse_queue.html", context=context)


@csrf_exempt
@superuser_or_bearer_required
def api_pay(request):
    try:
        rq = request.GET
        if request.method == "POST":
            rq = request.POST
        node = rq.get("node", None)
        tagstr = rq.get("src", None)
        amount_str = rq.get("amount", None)
        description = rq.get("description", None)
        amount = Money(amount_str, EUR)
    except Exception as e:
        logger.error(f"Tag payment has param issues: {e}")
        return HttpResponse("Params issues", status=400, content_type="text/plain")

    if None in [tagstr, amount_str, description, amount, node]:
        logger.error("Missing param, Payment at %s denied" % (node))
        return HttpResponse(
            "Mandatory params missing", status=400, content_type="text/plain"
        )

    if amount < Money(0, EUR):
        logger.error("Invalid param. Payment at %s denied" % (node))
        return HttpResponse("Invalid param", status=400, content_type="text/plain")

    if amount > settings.MAX_PAY_API:
        logger.error("Payment too high, rejected, Tag %s denied" % (tagstr))
        return HttpResponse(
            "Payment Limit exceeded", status=400, content_type="text/plain"
        )

    try:
        tag = Tag.objects.get(tag=tagstr)
    except ObjectDoesNotExist:
        logger.error("Tag %s not found, denied" % (tagstr))
        return HttpResponse("Tag not found", status=404, content_type="text/plain")

    if transact_raw(
        request,
        src=tag.owner,
        dst=User.objects.get(id=settings.POT_ID),
        description=description,
        amount=amount,
        reason="via API; tagid=%s (%s) @%s" % (tag.id, tag.owner, node),
        user=tag.owner,
    ):
        label = "%s" % tag.owner.first_name
        if len(label) < 1:
            label = "%s" % tag.owner.last_name
        if len(label) < 1:
            label = "%s" % tag.owner
        return JsonResponse({"result": True, "amount": amount.amount, "user": label})

    return HttpResponse("FAIL", status=500, content_type="text/plain")


@csrf_exempt
def api2_register(request):
    return new_api2_register(request)


@csrf_exempt
def api_get_skus(request):
    out = []
    for item in PettycashSku.objects.all():
        out.append(
            {
                "name": item.name,
                "description": item.description,
                "price": item.amount.amount,
            }
        )

    return JsonResponse(out, safe=False)


@csrf_exempt
def api_get_sku(request, sku):
    try:
        item = PettycashSku.objects.get(pk=sku)
        return JsonResponse(
            {
                "id": item.pk,
                "name": item.name,
                "description": item.description,
                "price": float(item.amount.amount),
            }
        )
    except ObjectDoesNotExist:
        logger.error("SKU %d not found, denied" % (sku))
        return HttpResponse("SKU not found", status=404, content_type="text/plain")

    return HttpResponse("Error", status=500, content_type="text/plain")


@csrf_exempt
@is_paired_terminal
def api2_pay(request, terminal):
    try:
        station = PettycashStation.objects.get(terminal=terminal)
    except ObjectDoesNotExist:
        logger.error("No station for terminal %s" % terminal)
        return HttpResponse(
            "Terminal not paired, rejecting", status=400, content_type="text/plain"
        )

    try:
        rq = request.GET
        if request.method == "POST":
            rq = request.POST
        tagstr = rq.get("src", None)
        amount_str = rq.get("amount", None)
        description = rq.get("description", None)
        amount = Money(amount_str, EUR)
    except Exception as e:
        logger.error(
            "Param issue for terminal %s@%s: %s"
            % (terminal.name, station.description, e)
        )
        return HttpResponse("Params problems", status=400, content_type="text/plain")

    if None in [tagstr, amount_str, description, amount]:
        logger.error(
            "Missing param for terminal %s@%s" % (terminal.name, station.description)
        )
        return HttpResponse(
            "Mandatory params missing", status=400, content_type="text/plain"
        )

    try:
        tag = Tag.objects.get(tag=tagstr)
    except ObjectDoesNotExist:
        logger.error(
            "Tag %s not found, terminal %s@%s"
            % (tagstr, terminal.name, station.description)
        )
        return HttpResponse("Tag not found", status=404, content_type="text/plain")

    if amount < Money(0, EUR):
        logger.error(
            "Amount under 0, terminal %s@%s - %s"
            % (terminal.name, station.description, tag.owner)
        )
        return HttpResponse("Invalid param", status=400, content_type="text/plain")

    if amount > settings.MAX_PAY_API:
        logger.error(
            "Payment too high, rejected, terminal %s@%s - %s"
            % (terminal.name, station.description, tag.owner)
        )
        return HttpResponse(
            "Payment Limit exceeded", status=400, content_type="text/plain"
        )

    if transact_raw(
        request,
        src=tag.owner,
        dst=User.objects.get(id=settings.POT_ID),
        description=description,
        amount=amount,
        reason="via API; tagid=%s (%s) @%s" % (tag.id, tag.owner, station.description),
        user=tag.owner,
    ):
        label = "%s" % tag.owner.first_name
        if len(label) < 1:
            label = "%s" % tag.owner.last_name
        if len(label) < 1:
            label = "%s" % tag.owner
        return JsonResponse({"result": True, "amount": amount.amount, "user": label})

    return HttpResponse("FAIL", status=500, content_type="text/plain")
