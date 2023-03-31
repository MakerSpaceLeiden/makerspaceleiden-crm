from django.shortcuts import render, redirect

from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMessage

from django.template import loader
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.utils import IntegrityError
from django.urls import reverse

from django.template.loader import render_to_string, get_template

from .forms import NewUserForm, NewAuditRecordForm

from acl.models import Entitlement, PermitType
from members.models import Tag, User, clean_tag_string, AuditRecord
from mailinglists.models import Mailinglist, Subscription

import logging
import datetime
import sys
import re

logger = logging.getLogger(__name__)


@login_required
def index(request):
    lst = Entitlement.objects.order_by("holder__id")
    agg = {}
    perms = {}
    output = ""
    for e in lst:
        if not e.holder in agg:
            agg[e.holder] = {}
        perms[e.permit.name] = 1
        agg[e.holder][e.permit.name] = 1

    context = {
        "agg": agg,
        "perms": perms,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "members/index.html", context)


@login_required
def newmember(request):
    if not request.user.is_privileged:
        logger.error(
            "{} tried to create a new member without the right priveleges. XS denied.".format(
                request.user
            )
        )
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    if request.POST:
        form = NewUserForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data.get("email")
                tag = form.cleaned_data.get("tag")
                newmember = User.objects.create_user(
                    email=email,
                    first_name=form.cleaned_data.get("first_name"),
                    last_name=form.cleaned_data.get("last_name"),
                )

                # Do not set this - it silently blocks the invite mails deep in PasswordResetForm.
                #
                # newmember.set_unusable_password()
                #
                newmember.set_password(User.objects.make_random_password())

                if form.cleaned_data.get("phone_number"):
                    newmember.phone_number = form.cleaned_data.get("phone_number")
                newmember.changeReason = (
                    "Added by {} with the newnmeber signup form".format(request.user)
                )
                newmember.save()

                # sanity check.
                newmember = User.objects.get(email=email)

                # Wire up the tag if one was provided.
                if form.cleaned_data.get("tag"):
                    tag.reassing_to_user(
                        newmember,
                        request.user,
                        activate=form.cleaned_data.get("activate_doors"),
                    )

                # Subscribe user if needed
                for mlist_name in form.cleaned_data.get("mailing_lists"):
                    try:
                        mlist = Mailinglist.objects.get(name=mlist_name)
                        s = Subscription.objects.create(
                            mailinglist=mlist,
                            member=newmember,
                            active=True,
                            digest=False,
                        )
                        s.subscribe()
                        # s.changeReason("Subscribed during form based new user create")
                        s.save()
                    except Exception as e:
                        logger.error(
                            "Failed to subscribe user {} to {} : {}".format(
                                request.user, mlist_name, e
                            )
                        )

                # Send welcome email.
                form = PasswordResetForm({"email": newmember.email})
                if not form.is_valid():
                    raise Exception("Internal issue")
                form.save(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    email_template_name="members/email_newmembers_invite.txt",
                    subject_template_name="members/email_newmembers_invite_subject.txt",
                )
                return redirect("index")
            except IntegrityError as e:
                logger.error("Failed to create user : {}".format(e))
                return HttpResponse(
                    "Create gone wrong. Was that email or name already added ?",
                    status=500,
                    content_type="text/plain",
                )
            except Exception as e:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                logger.error(
                    "Failed to create user : {} at {}:{}".format(filename, lineno, e)
                )
                return HttpResponse(
                    "Create gone wrong. Drat.", status=500, content_type="text/plain"
                )
        else:
            logger.debug("Form not valid")

    context = {
        "label": "Add a new member",
        "title": "New Member",
        "action": "Invite",
        "has_permission": request.user.is_authenticated,
    }
    context["form"] = NewUserForm()
    return render(request, "members/newmember.html", context)


@login_required
def sudo(request):
    if not request.user.can_escalate_to_priveleged:
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    if request.POST:
        form = NewAuditRecordForm(request.POST)

        if form.is_valid():
            try:
                record = form.save(commit=False)
                record.user = request.user
                record.changeReason = (
                    f"SUDO escalation in webinterface by {request.user}"
                )
                record.save()

                return redirect(form.cleaned_data.get("return_to"))
                # return redirect('index')

            except Exception as e:
                logger.error("Failed to create uudit recordser : {}".format(e))
                return HttpResponse(
                    "Could not create audit record.",
                    status=500,
                    content_type="text/plain",
                )

    rurl = reverse("index")
    if "HTTP_REFERER" in request.META:
        rurl = request.META["HTTP_REFERER"]
    form = NewAuditRecordForm(None, initial={"return_to": rurl})
    context = {
        "label": "GDPR (AVG)",
        "title": "Become and admin",
        "action": "go admin",
        "form": form,
        "back": "index",
        "has_permission": request.user.is_authenticated,
        "preamble": render_to_string("precooked_gdpr_options.html"),
    }
    return render(request, "crud.html", context)


def drop(request):
    if not request.user.can_escalate_to_priveleged:
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    record = AuditRecord(
        user=request.user, final=True, action="Drop privs from webinterface"
    )

    if request.user.is_privileged:
        record.changereason = f"DROP in webinterface by {request.user}"
    else:
        record.changereason = f"DROP in webinterface by {request.user} - but actual permission had already timed out."
    record.save()

    return redirect(request.META["HTTP_REFERER"])
