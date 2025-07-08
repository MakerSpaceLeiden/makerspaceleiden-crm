import json
import logging
import re
import sys
from datetime import timedelta

import six
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.forms import widgets
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from acl.models import Entitlement, Machine, PermitType, RecentUse
from agenda.models import Agenda
from chores.utils import get_chores_data
from makerspaceleiden.decorators import (
    is_superuser_or_bearer,
    superuser_or_bearer_required,
    superuser_required,
)
from members.models import Tag, User
from pettycash.models import PettycashBalanceCache
from selfservice.forms import (
    EmailNotificationSettingsForm,
    SignalNotificationSettingsForm,
    UserForm,
)
from ufo.models import Ufo

from .aggregator_adapter import get_aggregator_adapter
from .forms import TabledCheckboxSelectMultiple
from .models import WiFiNetwork
from .waiverform.waiverform import generate_waiverform_fd


def send_email_verification(
    request,
    user,
    new_email,
    old_email=None,
    template_user="email_verification_email.txt",
    template_trustee="email_verification_email_inform.txt",
):
    current_site = get_current_site(request)
    subject = "Confirm your email adddress ({})".format(current_site.domain)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    context = {
        "has_permission": request.user.is_authenticated,
        "request": request,
        "user": user,
        "new_email": new_email,
        "old_email": old_email,
        "domain": current_site.domain,
        # possibly changed with Django 2.2
        "uid": uid,
        "token": email_check_token.make_token(user),
        "noc_email": settings.DEFAULT_FROM_EMAIL,
        "trustees_email": settings.TRUSTEES,
    }
    if template_user:
        msg = render_to_string(template_user, context)
        EmailMessage(
            subject, msg, to=[new_email], from_email=settings.DEFAULT_FROM_EMAIL
        ).send()

    if old_email:
        subject = "[spacebot] User {} {} - new email address".format(
            user.first_name, user.last_name
        )
        msg = render_to_string(template_trustee, context)
        EmailMessage(
            subject,
            msg,
            to=[old_email, settings.TRUSTEES],
            from_email=settings.DEFAULT_FROM_EMAIL,
        ).send()


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk)
            + six.text_type(timestamp)
            + six.text_type(user.email)
        )


email_check_token = AccountActivationTokenGenerator()
logger = logging.getLogger(__name__)


def index(request):
    # Default values
    agenda_items = []
    ufo_items = []
    chores_data = []
    recent_activity = []
    cash_balance = "--,--"
    is_balance_positive = True
    has_tags = False
    title = "Welcome"

    if request.user.is_authenticated:
        today = timezone.now().date()
        three_months_later = today + timedelta(days=90)

        # Fetch items with dates from today in the next three months, and fetch maximum 5 items
        agenda_items = Agenda.objects.filter(
            enddate__gte=today, startdate__lte=three_months_later
        ).order_by("startdate", "starttime", "item_title")[:5]

        # Fetch Ufo items
        ufo_items = Ufo.objects.filter(
            state="UNK", dispose_by_date__gte=timezone.now()
        ).order_by("created_at")[:8]

        # Get chores data using the chores/utils/get_chores_data function
        chores_data, error_message = get_chores_data(current_user_id=request.user.id)

        # Initialize cash balance
        cash_balance = "--,--"
        is_balance_positive = True

        try:
            cash_balance_obj = PettycashBalanceCache.objects.get(
                owner=request.user
            ).balance
            cash_balance = cash_balance_obj if cash_balance_obj else "--,--"
            is_balance_positive = (
                cash_balance_obj.amount >= 0 if cash_balance_obj else False
            )

        except (ObjectDoesNotExist, ValueError):
            cash_balance = "--,--"
            is_balance_positive = True

        try:
            # Get the 5 most recent activities for the user
            recent_activity = RecentUse.objects.filter(user=request.user).order_by(
                "-used"
            )[:5]
        except RecentUse.DoesNotExist:
            recent_activity = []

        tags = Tag.objects.filter(owner=request.user)
        has_tags = tags.exists()

        title = "Dashboard"

    context = {
        "has_permission": request.user.is_authenticated,
        "title": title,
        "user": request.user,
        "agenda_items": agenda_items,
        "event_groups": chores_data if chores_data else [],
        "ufo_items": ufo_items,
        "cash_balance": cash_balance,
        "is_balance_positive": is_balance_positive,
        "recent_activity": recent_activity,
        "has_tags": has_tags,
    }
    if request.user.is_authenticated:
        context["is_logged_in"] = request.user.is_authenticated
        context["member"] = request.user
        context["wifinetworks"] = WiFiNetwork.objects.order_by("network")
        context["mainsadmin"] = request.user.groups.filter(
            name=settings.SENSOR_USER_GROUP
        ).exists()

    return render(request, "index.html", context)


@login_required
def pending(request):
    pending = (
        Entitlement.objects.all().filter(active=False).filter(holder__is_active=True)
    )

    es = []
    for p in pending:
        es.append((p.id, p))

    form = forms.Form(request.POST)
    form.fields["entitlement"] = forms.MultipleChoiceField(
        label="Entitlements",
        choices=es,
        widget=widgets.SelectMultiple(attrs={"size": len(es)}),
    )
    context = {
        "title": "Pending entitlements",
        "user": request.user,
        "has_permission": request.user.is_authenticated,
        "pending": pending,
        "lst": es,
        "form": form,
    }
    if request.method == "POST" and form.is_valid():
        if not request.user.is_staff:
            return HttpResponse(
                "You are propably not an admin ?", status=403, content_type="text/plain"
            )

        for eid in form.cleaned_data["entitlement"]:
            e = Entitlement.objects.get(pk=eid)
            e.active = True
            e.changeReason = (
                "Activated through the self-service interface by {0}".format(
                    request.user
                )
            )
            e.save()
        context["saved"] = True

    return render(request, "pending.html", context)


@login_required
def recordinstructions(request):
    member = request.user

    # keep the option open to `do bulk adds
    members = User.objects.filter(is_active=True)
    all_machines = Machine.objects.all().exclude(requires_permit=None).order_by("name")

    machines = all_machines
    # Only show machine we are entitled for ourselves.
    #
    if not request.user.is_privileged:
        machines = [m for m in all_machines if m.canInstruct(member)]
        members = members.exclude(id=member.id)

    ps = []
    for m in members:
        ps.append((m.id, m.first_name + " " + m.last_name))

    ms = []
    for m in machines:
        ms.append((m.id, m.name))

    form = forms.Form(request.POST)  # machines, members)
    form.fields["machine"] = forms.MultipleChoiceField(
        label="Machine",
        choices=ms,
        help_text="Select multiple if so desired",
        widget=TabledCheckboxSelectMultiple(),
    )
    form.fields["persons"] = forms.MultipleChoiceField(
        label="Person", choices=ps, help_text="Select multiple if so desired"
    )

    if request.user.is_privileged:
        form.fields["issuer"] = forms.ChoiceField(label="Issuer", choices=ps)

    context = {
        "machines": machines,
        "members": members,
        "title": "Record instructions",
        "is_logged_in": request.user.is_authenticated,
        "user": request.user,
        "has_permission": True,
        "form": form,
        "lst": ms,
    }

    saved = False
    if request.method == "POST" and form.is_valid():
        context["machines"] = []
        context["holder"] = []
        holder = []

        for mid in form.cleaned_data["machine"]:
            try:
                m = Machine.objects.get(pk=mid)
                if request.user.is_privileged and form.cleaned_data["issuer"]:
                    i = User.objects.get(pk=form.cleaned_data["issuer"])
                else:
                    i = request.user

                pt = None
                if m.requires_permit:
                    pt = PermitType.objects.get(pk=m.requires_permit.id)

                if pt is None:
                    logger.error(f"{m} skipped - no permit - bug ?")
                    continue

                for pid in form.cleaned_data["persons"]:
                    p = User.objects.get(pk=pid)

                    # Note: We allow for 'refreshers' -- and rely on the history record.
                    #
                    created = False
                    try:
                        record = Entitlement.objects.get(permit=pt, holder=p)
                        record.issuer = i
                        record.changeReason = (
                            "Updated through the self-service interface by {0}".format(
                                i
                            )
                        )
                    except Entitlement.DoesNotExist:
                        record = Entitlement(permit=pt, holder=p, issuer=i)
                        created = True
                        record.changeReason = (
                            "Created in the self-service interface by {0}".format(i)
                        )
                    except Exception as e:
                        logger.error(
                            "Something else went wrong during create: {0}".format(e)
                        )
                        return HttpResponse(
                            "Something went wrong. Could not understand this update. Sorry.",
                            status=500,
                            content_type="text/plain",
                        )

                    record.active = not pt.require_ok_trustee
                    try:
                        record.save(request=request)
                        logger.error("Creation of {0} completed".format(record))
                        holder.append(p)

                    except Exception as e:
                        logger.error("Updating of instructions failed: {0}".format(e))
                        return HttpResponse(
                            "Something went wrong. Could not record these instructions. Sorry.",
                            status=500,
                            content_type="text/plain",
                        )

                context["created"] = created
                context["machines"].append(m)
                context["issuer"] = i
                context["holder"] = list(
                    set(holder)
                )  # Using set() to remove duplicates

                saved = True
            except Entitlement.DoesNotExist as e:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename

                logger.error(
                    "Unexpected error during save of intructions:: {} at {}:{}".format(
                        filename, lineno, e
                    )
                )
                return HttpResponse(
                    "Something went wrong. Could not undertand these instructions. Sorry.",
                    status=500,
                    content_type="text/plain",
                )

    context["saved"] = saved
    return render(request, "record.html", context)


@login_required
def confirmemail(request, uidb64, token, new_email):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if request.user != user:
            return HttpResponse(
                "You can only change your own records.",
                status=500,
                content_type="text/plain",
            )
        old_email = user.email
        if email_check_token.check_token(user, token):
            user.email = new_email
            user.email_confirmed = True
            user.save()
            send_email_verification(
                request,
                user,
                new_email,
                old_email,
                template_user="email_confirm_email.txt",
                template_trustee="email_confirm_email_inform.txt",
            )
            return render(request, "email_verification_ok.html")
        else:
            return HttpResponse(
                "Failed to confirm", status=500, content_type="text/plain"
            )

        logger.debug(
            "Change of email from '{}' to '{}' confirmed.".format(old_email, new_email)
        )
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        # We perhaps should not provide the end user with feedback -- e.g. prentent all
        # went well. As we do not want to function as an oracle.
        #
        logger.error("Something else went wrong in confirm email: {0}".format(e))

    return HttpResponse(
        "Something went wrong. Sorry.", status=500, content_type="text/plain"
    )


@login_required
def waiverformredir(request):
    return redirect("waiverform", user_id=request.user.id)


@login_required
def waiverform(request, user_id=None):
    try:
        member = User.objects.get(pk=user_id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")
    confirmation_url = request.build_absolute_uri(
        reverse("waiver_confirmation", kwargs=dict(user_id=user_id))
    )
    name = f"{member.first_name} {member.last_name}"
    safename = re.sub("\W+", "-", name)

    fd = generate_waiverform_fd(member.id, name, confirmation_url)

    response = HttpResponse(fd.getvalue(), status=200, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="MSL-Waiver-{safename}.pdf"'
    )

    return response


@login_required
def confirm_waiver(request, user_id=None):
    try:
        operator_user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        member = User.objects.get(pk=user_id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    if not operator_user.is_staff:
        return HttpResponse(
            "You must be staff to confirm a waiver",
            status=400,
            content_type="text/plain",
        )

    member.form_on_file = True
    member.save()

    return render(request, "waiver_confirmation.html", {"member": member})


@login_required
def telegram_connect(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    token = aggregator_adapter.generate_telegram_connect_token(user.id)
    return HttpResponse(token, status=200, content_type="text/plain")


@login_required
def telegram_disconnect(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    aggregator_adapter.disconnect_telegram(user.id)
    return render(
        request,
        "telegram_disconnect.html",
        {
            "title": "Telegram BOT",
        },
    )


@login_required
def signal_disconnect(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    user.uses_signal = False
    user.save()

    return render(
        request,
        "signal_disconnect.html",
        {
            "title": "Signal BOT",
        },
    )


@login_required
def notification_settings(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    signal_form = SignalNotificationSettingsForm(instance=user)
    email_form = EmailNotificationSettingsForm(instance=user)

    return render(
        request,
        "notification_settings.html",
        {
            "title": "Notification Settings",
            "uses_signal": user.phone_number and user.uses_signal,
            "signal_form": signal_form,
            "email_form": email_form,
            "uses_email": (not user.uses_signal and not user.telegram_user_id)
            or user.always_uses_email,
            "user": user,
            "has_permission": request.user.is_authenticated,
        },
    )


@login_required
def save_signal_notification_settings(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    if request.method == "POST":
        user_form = SignalNotificationSettingsForm(
            request.POST, request.FILES, instance=user
        )
        if user_form.is_valid():
            user_form.save()
            uses_signal = bool(user_form.data.get("uses_signal"))
            if uses_signal:
                aggregator_adapter.onboard_signal(user.id)

    return redirect("overview", member_id=user.id)


@login_required
def save_email_notification_settings(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    if request.method == "POST":
        user_form = EmailNotificationSettingsForm(
            request.POST, request.FILES, instance=user
        )
        if user_form.is_valid():
            user_form.save()
            return redirect("overview", member_id=user.id)


@login_required
def notification_test(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    aggregator_adapter.notification_test(user.id)
    return redirect("notification_settings")


@login_required
def space_state(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    context = {}
    aggregator_adapter = get_aggregator_adapter()

    try:
        context = aggregator_adapter.fetch_state_space()
    except Exception as e:
        logger.error("No data available, exception: {0}".format(str(e)))
        context["no_data_available"] = True

    # Sort 'machines' by machine name alphabetically
    if "machines" in context and isinstance(context["machines"], list):
        context["machines"] = sorted(
            context["machines"],
            key=lambda machine_state: machine_state["machine"]["name"].lower(),
        )

    context["user"] = user
    context["title"] = "State of the Space"
    context["has_permission"] = request.user.is_authenticated

    return render(request, "space_state.html", context)


def space_state_api(request):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )
    context = aggregator_adapter.fetch_state_space()

    payload = {}
    l = 0
    for e in ["space_open", "lights_on", "machines", "users_in_space"]:
        if e in context:
            payload[e] = context[e]
            if e == "users_in_space":
                l = len(context[e])
    if not is_superuser_or_bearer(request):
        payload = {}

    payload["num_users_in_space"] = l

    return HttpResponse(
        json.dumps(payload).encode("utf8"), content_type="application/json"
    )


@superuser_or_bearer_required
def space_state_api_info(request):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )
    context = aggregator_adapter.fetch_state_space()

    try:
        payload = {"machines": [], "members": [], "lights": []}
        if "machines" in context:
            for mj in context["machines"]:
                if "ready" in mj["state"]:
                    continue
                if "off" in mj["state"]:
                    continue
                if "deur" in mj["machine"]["name"]:
                    continue
                payload["machines"].append(mj["machine"]["name"])
        if "users_in_space" in context:
            for ij in context["users_in_space"]:
                if "user" in ij:
                    payload["members"].append(ij["user"]["first_name"])
        if "lights_on" in context:
            payload["lights"] = context["lights_on"]

        return HttpResponse(
            json.dumps(payload).encode("utf8"), content_type="application/json"
        )

    except Exception as e:
        logger.error(
            f"Something went wrong during json return parse from aggregator - likely compat issue: {e}"
        )

    return HttpResponse("No aggregator response", status=500, content_type="text/plain")


@login_required
def space_checkout(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=400,
            content_type="text/plain",
        )

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    aggregator_adapter.checkout(user.id)
    return redirect("space_state")


@login_required
@superuser_required
def userdetails_admin_edit(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        old_email = "{}".format(user.email)
    except ObjectDoesNotExist:
        logger.error("Edit RQ by admin for unknown user id={}".format(user_id))
        return HttpResponse(
            "User not found",
            status=404,
            content_type="text/plain",
        )
    return userdetails_edit(request, user, old_email, verify=False)


@login_required
def userdetails(request):
    cancel_button_url = request.GET.get("redirect_to", "index")
    if not cancel_button_url:
        cancel_button_url = "/"
    try:
        member = request.user
        old_email = "{}".format(member.email)
    except User.DoesNotExist:
        return HttpResponse(
            "You are probably not a member-- admin perhaps?",
            status=500,
            content_type="text/plain",
        )
    return userdetails_edit(request, member, old_email)


def userdetails_edit(request, member, old_email, verify=True):
    cancel_button_url = request.GET.get("redirect_to", "index")
    if not cancel_button_url:
        cancel_button_url = "/"
    if request.method == "POST":
        try:
            user_asis = UserForm(request.POST, request.FILES, instance=member)
            save_user = user_asis.save(commit=False)
            if user_asis.is_valid():
                new_email = "{}".format(user_asis.cleaned_data["email"])

                save_user.email = old_email
                save_user.changeReason = (
                    "Updated through the self-service interface by {0}".format(
                        request.user
                    )
                )
                save_user.save()

                user = UserForm(request.POST, instance=save_user)
                for f in user.fields:
                    user.fields[f].disabled = True

                if old_email != new_email:
                    if verify:
                        member.email_confirmed = False
                        member.changeReason = "Reset email validation, email changed."
                        member.save()
                        send_email_verification(request, member, new_email, old_email)

                        return render(request, "email_verification_email.html")
                    else:
                        member.email = new_email
                        member.email_confirmed = True
                        member.save()
                        send_email_verification(
                            request,
                            member,
                            new_email,
                            old_email,
                            template_user="email_confirm_email_inform.txt",
                            template_trustee="email_confirm_email_inform.txt",
                        )

                return render(
                    request,
                    "userdetails.html",
                    {"form": user_asis, "saved": True, "user_id": member.id},
                )
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename

            logger.error(
                "Unexpected error during save of user '{}' by {}: {} at {}:{}".format(
                    member, request.user, filename, lineno, e
                )
            )
            return HttpResponse(
                "Unexpected error during save of userdetails (does the phone number start with a +<country code>?)",
                status=500,
                content_type="text/plain",
            )

    cancel_button_url = request.GET.get("redirect_to", "index")
    form = UserForm(instance=member)
    context = {
        "title": "Selfservice - update details",
        "is_logged_in": request.user.is_authenticated,
        "user": member,
        "form": form,
        "has_permission": True,
        "user_id": member.id,
        "cancel_button_url": cancel_button_url,
    }
    return render(request, "userdetails.html", context)


class AmnestyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        machines = kwargs.pop("machines")
        super(AmnestyForm, self).__init__(*args, **kwargs)
        for m in machines:
            self.fields["machine_%s" % m.id] = forms.BooleanField(
                label=m.name, required=False
            )


@login_required
def amnesty(request):
    machines = Machine.objects.exclude(requires_permit=None)
    machines_entitled = Machine.objects.all().filter(
        requires_permit__isRequiredToOperate__holder=request.user
    )

    context = {"title": "Amnesty", "saved": False}

    form = AmnestyForm(request.POST or None, machines=machines)
    if form.is_valid():
        permits = []
        for m in machines:
            if not form.cleaned_data["machine_%s" % m.id]:
                continue
            if m in machines_entitled:
                continue
            if not m.requires_permit or m.requires_permit in permits:
                continue
            permits.append(m.requires_permit)
        for p in permits:
            e, created = Entitlement.objects.get_or_create(
                holder=request.user, issuer=request.user, permit=p
            )
            if created:
                e.changeReason = (
                    "Added through the grand amnesty interface by {0}".format(
                        request.user
                    )
                )
                e.active = True
                e.save()
                context["saved"] = True

    for m in machines_entitled:
        form.fields["machine_%s" % m.id].initial = True
        form.fields["machine_%s" % m.id].disabled = True
        form.fields[
            "machine_%s" % m.id
        ].help_text = "Already listed - cannot be edited."

    context["form"] = form

    return render(request, "amnesty.html", context)


@superuser_required
def send_reset_email(request, uid):
    user = User.objects.get(pk=uid)
    template = "registration/password_reset_email.html"
    form = PasswordResetForm({"email": user.email})
    if form.is_valid():
        form.save(email_template_name=template)

    return redirect("overview", member_id=uid)
