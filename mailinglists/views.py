from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django import forms
from django.forms import ModelForm
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.db.models import Q

from time import strptime
import datetime


from django.views.decorators.csrf import csrf_exempt
from makerspaceleiden.decorators import superuser_or_bearer_required, superuser

from .forms import SubscriptionForm
from .mailman import MailmanService, MailmanAccount

import json, os, re

from members.models import User

from acl.models import Machine, Entitlement, PermitType

from .models import Mailinglist, Subscription

from storage.models import Storage
from memberbox.models import Memberbox

import logging

logger = logging.getLogger(__name__)


@login_required
def mailinglists_edit(request, user_id=None):
    user = request.user
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponse("User not found", status=404, content_type="text/plain")

    if user != request.user and request.user.is_privileged != True:
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    lists = Mailinglist.objects.all()
    subs = Subscription.objects.all().filter(member=user)

    # In theory we could assume a perfectly synced DB; but we'll for now
    # allow discrepancies - and simply add any missing subscriptions if
    # needed on the next save of this form.
    #
    id2list = {}
    id2sub = {}
    for l in lists:
        id2list[str(l.id)] = l
        id2sub[str(l.id)] = None

    for s in subs:
        id2sub[str(s.mailinglist.id)] = s

    if request.method == "POST":
        forms = [
            SubscriptionForm(request.POST, prefix=str(l.id), instance=id2sub[str(l.id)])
            for l in lists
        ]
        if all([form.is_valid() for form in forms]):
            if not request.user.is_privileged:
                for form in forms:
                    if id2list[form.prefixd2l].hidden:
                        return HttpResponse(
                            "XS denied", status=403, content_type="text/plain"
                        )

            for form in forms:
                nw = form.save(commit=False)
                nw.member = user
                nw.mailinglist = id2list[form.prefix]
                logger.error(f"Saving {nw}: a={nw.active} d={nw.digest}")
                nw.save()
            return redirect("mailinglists_edit", user_id=user.id)

    forms = []
    for l in lists:
        # As per above 'not perfect' note -- See if we already have this subscription or not; and then use that
        # to populate our values; otherwise pick up a brand new one.
        #
        if l.hidden and not request.user.is_privileged:
            continue
        s = [s for s in subs if s.mailinglist == l]
        if s:
            s = s[0]
        if s:
            form = SubscriptionForm(prefix=str(l.id), instance=s)
        else:
            form = SubscriptionForm(prefix=str(l.id))

        forms.append((l, form))

    return render(
        request,
        "multi_crud.html",
        {
            "title": "Edit mailing lists subscriptions",
            "forms": forms,
            "action": "Submit",
            "user": request.user,
            "member": user,
            "back": "mailinglists_edit",
            "has_permission": request.user.is_authenticated,
        },
    )


@login_required
def mailinglists_archives(request):
    return render(
        request,
        "lists.html",
        {
            "title": "Mailing list archives",
            "items": Mailinglist.objects.all(),
            "back": "home",
            "has_permission": request.user.is_authenticated,
        },
    )


@login_required
@superuser
def mailinglists_subs(request):
    lists = Mailinglist.objects.all()
    users = User.objects.all()
    rows = []
    for user in users:
        item = [user]
        for l in lists:
            v = "NO"
            if Subscription.objects.filter(
                member=user, mailinglist=l, active=True
            ).exists():
                v = "yes"
            item.append(v)
        rows.append(item)

    return render(
        request,
        "subs.html",
        {
            "title": "Mailing list subscriptions",
            "lists": lists,
            "users": users,
            "subs": rows,
            "back": "home",
            "has_permission": request.user.is_authenticated,
        },
    )


# Todo: attachment (full URL intercept) & rewrite them.
@login_required
def mailinglists_archive(
    request, mlist, yearmonth=None, order=None, zip=None, attachment=None
):
    # XXX - cache this 'per list' or make the loging 'admin level' cross lists.
    #
    service = MailmanService(settings.ML_PASSWORD, settings.ML_ADMINURL)

    try:
        mid = Mailinglist.objects.get(name=mlist)
        mlist = mid.name
    except Mailinglist.DoesNotExist:
        return HttpResponse("List not found", status=404, content_type="text/plain")

    # TODO - implement security for hidden lists ??

    # Real URL
    #     https://mailman.makerspaceleiden.nl/mailman/private/<mlist>
    #
    path = f"private/{ mlist }/"
    if yearmonth:
        try:
            m = strptime(yearmonth, "%Y-%B")
            fdom = datetime.datetime.strptime(yearmonth + "-01", "%Y-%B-%d")
            year = m.tm_year
            month = m.tm_mon
        except Exception as e:
            logger.error(f"Path element { yearmonth } not understood")
            return HttpResponse(
                "Path not understood", status=500, content_type="text/plain"
            )

        if mid.visible_months:
            f = datetime.date.today() - datetime.timedelta(
                days=mid.visible_months * 30
            )  # Bit in-exact; but not very critical as we round down to months.
            if (
                year < f.year
                or (year == f.year and month < f.month)
                and not request.user.is_privileged
            ):
                return HttpResponse(
                    "No access to archives this old; contact the trustees",
                    status=404,
                    content_type="text/plain",
                )

        if zip:
            path = path + yearmonth + ".txt.gz"
        else:
            path = path + yearmonth + "/"

    if attachment:
        path = f"private/{mlist}/attachments/{attachment}"
    elif order:
        path = path + order + ".html"

    response = service.get(mlist, path)
    mimetype = response.info().get_content_type().lower()

    if not mimetype:
        mimetype = "text/plain"

    body = response.read()
    if mimetype == "text/html" and not attachment:
        try:
            body = body.decode("utf-8")
        except UnicodeDecodeError:
            try:
                body = body.decode("latin1")
            except UnicodeDecodeError:
                body = body.decode(errors="ignore")

        if yearmonth == None:
            p = reverse("mailinglists_archives")
            body = re.sub(r"You can get", "", body)
            body = re.sub(
                r'<a href="\S+listinfo\S+"[^<]*</a>',
                f'<a href="{p}">Overview of all list archives</a>.',
                body,
            )
        else:
            p = reverse("mailinglists_archive", kwargs={"mlist": mlist})
            body = re.sub(
                r'<a href="\S+listinfo\S+"[^<]*</a>',
                f'<a href="{p}">Overview for the archive of this list</a>.',
                body,
            )

        if order:
            pattern = f"{service.adminurl}/private/{mlist}/(attachments/\d+/[a-fA-F0-9]+/attachment[\-\d+.\w]+)"
            r = re.compile(pattern)
            body = re.sub(r, "\g<1>", body)

        body = re.sub(re.compile("<!--x-search-form-->.*</form>", re.DOTALL), "", body)

    return HttpResponse(body, content_type=mimetype)
