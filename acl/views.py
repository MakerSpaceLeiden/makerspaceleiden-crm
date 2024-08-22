import logging
from functools import wraps

from dateutil.tz.tz import EPOCH
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from ipware import get_client_ip

from mailinglists.models import Subscription
from makerspaceleiden.decorators import superuser_or_bearer_required, superuser_required
from memberbox.models import Memberbox
from members.forms import TagForm
from members.models import Tag, User, clean_tag_string
from pettycash.models import PettycashBalanceCache
from storage.models import Storage
from terminal.decorators import is_paired_terminal

from .models import (
    Entitlement,
    Machine,
    PermitType,
    RecentUse,
    change_tracker_counter,
    useNeedsToStateStr,
)

logger = logging.getLogger(__name__)


def matrix_mm(machine, member):
    out = {"xs": False, "instructions_needed": False, "tags": []}
    out["mid"] = machine.id

    out["requires_instruction"] = machine.requires_instruction
    out["requires_permit"] = machine.requires_permit
    out["requires_form"] = machine.requires_form
    out["out_of_order"] = machine.out_of_order
    out["can_instruct"] = machine.canInstruct(member)
    out["xs"] = machine.canOperate(member)
    out["activated"] = out["xs"]

    for tag in Tag.objects.filter(owner=member):
        out["tags"].append(tag.tag)

    return out


def matrix_m(machine):
    lst = {}
    for mbr in User.objects.filter(is_active=True).order_by():
        lst[mbr] = matrix_mm(machine, mbr)

    return lst


def get_perms(tag, machine):
    owner = tag.owner
    canOperate = machine.canOperate(owner)
    canInstruct = machine.canInstruct(owner)

    out = userdetails(owner)
    if tag.description:
        out["tag"] = tag.description

    out["requires_instruction"] = machine.requires_instruction
    out["requires_permit"] = str(machine.requires_permit)
    out["requires_form"] = machine.requires_form
    out["machine"] = str(machine)
    out["access"] = canOperate
    out["can_instruct"] = canInstruct

    return out


@login_required
def api_index(request):
    lst = Machine.objects.order_by()
    perms = {}
    instructions = []
    ffa = []
    for m in lst:
        if m.requires_permit:
            if m.requires_permit.name not in perms:
                perms[m.requires_permit.name] = []
            perms[m.requires_permit.name].append(m)
        else:
            if m.requires_instruction:
                instructions.append(m)
            else:
                ffa.append(m)

    context = {
        "lst": lst,
        "perms": perms,
        "instructions": instructions,
        "freeforall": ffa,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "acl/index.html", context)


def api_index_legacy2(request):
    ip, local = get_client_ip(request, proxy_trusted_ips=("127.0.0.1", "::1"))
    if not (local or (request.user and request.user.is_superuser)):
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    out = ""
    for member in User.objects.filter(is_active=True):
        machines = []
        for machine in (
            Machine.objects.all()
            .exclude(requires_permit=None)
            .exclude(node_machine_name=None)
        ):
            if machine.requires_form and not member.form_on_file:
                continue

            entitlements = Entitlement.objects.filter(holder=member).filter(active=True)

            if machine.requires_permit:
                entitlements = entitlements.filter(permit=machine.requires_permit)

            # shoudl we also check the other biz rules - such as permit by permit ?
            if entitlements.count() <= 0:
                continue

            if machine.node_machine_name:
                machines.append(machine.node_machine_name)
        if not machines:
            continue

        machines_string = ",".join(machines).lower()

        tags = Tag.objects.filter(owner=member)
        for tag in tags:
            out += "{}:{}:{} # {}\n".format(
                tag.tag, machines_string, member.name(), tag.id
            )

    return HttpResponse(out, content_type="text/plain")


@login_required
def machine_list(request):
    machines = Machine.objects.order_by("name")
    members = User.objects.all().filter(is_active=True).order_by("first_name")

    context = {
        "members": members,
        "machines": machines,
        "has_permission": request.user.is_authenticated,
        "title": "Machines",
    }
    return render(request, "acl/machines.html", context)


@login_required
def machine_overview(request, machine_id=None):
    instructors = []
    used = []
    machines = Machine.objects.order_by("name")
    if machine_id:
        try:
            machines = machines.filter(pk=machine_id)
        except ObjectDoesNotExist:
            return HttpResponse(
                "Machine not found", status=404, content_type="text/plain"
            )
        machine = machines.first()
        permit = machine.requires_permit
        if permit:
            permit = PermitType.objects.get(pk=permit.id)
            if permit.permit:
                instructors = Entitlement.objects.filter(permit=permit.permit)
            else:
                instructors = Entitlement.objects.filter(permit=permit)
            instructors = (instructors.order_by("holder__first_name"),)
        if request.user.is_privileged:
            used = RecentUse.objects.all().filter(machine=machine).order_by("-used")

    lst = {}
    for mchn in machines:
        lst[mchn.name] = matrix_m(mchn)

    members = User.objects.all().filter(is_active=True).order_by("first_name")

    context = {
        "members": members,
        "machines": machines,
        "lst": lst,
        "used": used,
        "instructors": instructors,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "acl/matrix.html", context)


@login_required
def members(request):
    members = User.objects.order_by("first_name")
    active = members.filter(is_active=True)
    if not request.user.is_privileged:
        members = active

    context = {
        "title": "Members list",
        "members": members,
        "num_active": len(active),
        "num_members": len(members),
        "num_inactive": len(members) - len(active),
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "acl/members.html", context)


def _overview(request, member_id=None):
    if member_id is None:
        member_id = request.user.id
    try:
        member = User.objects.get(pk=member_id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    if not member.is_active and not request.user.is_privileged:
        return HttpResponse(
            "User not found or access denied", status=404, content_type="text/plain"
        )

    machines = Machine.objects.order_by()
    boxes = Memberbox.objects.all().filter(owner=member)
    storage = Storage.objects.all().filter(owner=member)
    subscriptions = Subscription.objects.all().filter(member=member)

    normal_permits = {}
    for m in machines:
        normal_permits[m.requires_permit] = True

    specials = []
    for e in Entitlement.objects.all().filter(holder=member):
        if e.permit not in normal_permits:
            specials.append(e)

    lst = {}
    for mchn in machines:
        lst[mchn.name] = matrix_mm(mchn, member)
        lst[mchn.name]["path"] = mchn.path()

    user = request.user
    balance = 0
    try:
        balance = PettycashBalanceCache.objects.get(owner=user)

    except ObjectDoesNotExist:
        pass

    context = {
        "title": member.first_name + " " + member.last_name,
        "member": member,
        "machines": machines,
        "storage": storage,
        "boxes": boxes,
        "lst": lst,
        "permits": specials,
        "subscriptions": subscriptions,
        "user": request.user,
        "has_permission": request.user.is_authenticated,
        "balance": balance,
    }

    if member == request.user or request.user.is_privileged:
        tags = Tag.objects.filter(owner=member)
        context["tags"] = tags
        context["used"] = RecentUse.objects.all().filter(user=member).order_by("-used")

    # Notification settings
    context["uses_signal"] = request.user.phone_number and request.user.uses_signal
    context["uses_telegram"] = bool(request.user.telegram_user_id)
    context["uses_email"] = (
        not context["uses_signal"] and not context["uses_telegram"]
    ) or request.user.always_uses_email

    return context


@login_required
def member_overview(request, member_id=None):
    return render(request, "acl/member_overview.html", _overview(request, member_id))


@superuser_required
def member_delete_confirm(request, member_id=None):
    return render(request, "acl/delete_overview.html", _overview(request, member_id))


@superuser_required
def member_delete(request, member_id=None):
    try:
        member = User.objects.get(pk=member_id)
    except ObjectDoesNotExist:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    try:
        member.delete()
    except Exception as e:
        raise Http404("Delete failed: {}".format(str(e)))

    return redirect("index")


@superuser_or_bearer_required
def api_details(request, machine_id):
    try:
        machine = Machine.objects.get(pk=machine_id)
    except Exception as e:
        raise Http404("Machine not found. {}".format(str(e)))

    context = {"machine": machine.name, "lst": matrix_m(machine)}
    return render(request, "acl/details.txt", context, content_type="text/plain")


def missing(tof):
    holders = (
        User.objects.all()
        .filter(is_active=True)
        .filter(form_on_file=tof)
        .filter(isGivenTo__permit__has_permit__requires_form=True)
        .distinct()
    )
    return holders


@login_required
def missing_forms(request):
    context = {
        "title": "Missing waivers",
        "desc": "Missing waiver forms (of people who had instruction on a machine that needs it).",
        "amiss": missing(False),
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "acl/missing.html", context)


@login_required
def missing_doors(request):
    missing = (
        User.objects.all()
        .filter(is_active=True)
        .exclude(isGivenTo__permit=settings.DOORS)
        .order_by("-id")
    )

    context = {
        "title": "No doors or tags",
        "desc": "People with no doors and/or tags",
        "amiss": missing,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "acl/missing.html", context)


@login_required
def filed_forms(request):
    # people_with_forms = User.objects.all().filter(form_on_file = True)
    context = {
        "title": "Filed waivers",
        "desc": "Waiver forms on file for people that also had instruction on something",
        "amiss": missing(True),
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "acl/missing.html", context)


@login_required
def tag_edit(request, tag_id=None):
    try:
        tag = Tag.objects.get(pk=tag_id)
    except ObjectDoesNotExist:
        return HttpResponse("Tag not found", status=404, content_type="text/plain")

    context = {
        "title": "Update a tag",
        "action": "Update",
        "item": tag,
        "has_permission": request.user.is_authenticated,
    }
    if request.POST:
        form = TagForm(
            request.POST or None,
            request.FILES,
            instance=tag,
            canedittag=request.user.is_privileged,
        )
        if form.is_valid() and request.POST:
            try:
                item = form.save(commit=False)
                item.changeReason = "Changed by {} via self service portal".format(
                    request.user
                )
                item.save()
            except Exception as e:
                logger.error("Unexpected error during update of tag: {}".format(e))

            return redirect("overview", member_id=item.owner_id)

    form = TagForm(instance=tag, canedittag=request.user.is_privileged)
    context["form"] = form
    context["back"] = "personal_page"

    return render(request, "crud.html", context)


@login_required
def tag_delete(request, tag_id=None):
    try:
        tag = Tag.objects.get(pk=tag_id)
    except ObjectDoesNotExist:
        return HttpResponse("Tag not found", status=404, content_type="text/plain")

    context = {
        "title": "Delete a tag -- confirm",
        "action": "Yes - really Delete",
        "item": tag,
        "has_permission": request.user.is_authenticated,
    }
    if request.POST:
        form = TagForm(request.POST or None, request.FILES, instance=tag, isdelete=True)
        if form.is_valid() and request.POST:
            try:
                item = form.save(commit=False)
                item.delete()
            except Exception as e:
                logger.error("Unexpected error during deleteof tag: {}".format(e))

            return redirect("overview", member_id=item.owner_id)

    form = TagForm(instance=tag, isdelete=True)
    context["form"] = form
    context["back"] = "personal_page"

    return render(request, "crud.html", context)


def userdetails(owner):
    return {
        "userid": owner.id,
        "user": True,
        "name": str(owner),
        "first_name": owner.first_name,
        "last_name": owner.last_name,
        "email": owner.email,
    }


@csrf_exempt
@superuser_or_bearer_required
def api_gettaginfo(request):
    if request.POST:
        tagstr = clean_tag_string(request.POST.get("tag"))

        if not tagstr:
            return HttpResponse("No valid tag", status=400, content_type="text/plain")

        try:
            tag = Tag.objects.get(tag=tagstr)
            owner = tag.owner
        except ObjectDoesNotExist:
            return HttpResponse(
                "Tag/Owner not found", status=404, content_type="text/plain"
            )

        out = userdetails(owner)
        if tag.description:
            out["tag"] = tag.description
        out["seenBefore"] = True
        return JsonResponse(out)

    return JsonResponse({})


def checktag(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.POST:
            return HttpResponse("XS denied", status=403, content_type="text/plain")

        try:
            tagstr = clean_tag_string(request.POST.get("tag"))
        except Exception:
            logger.error("No or invalid tag passed to getok, denied.")
            return HttpResponse(
                "No or invalid tag", status=400, content_type="text/plain"
            )

        if not tagstr:
            logger.error("No valid tag passed to getok, denied.")
            return HttpResponse("No valid tag", status=400, content_type="text/plain")

        try:
            tag = Tag.objects.get(tag=tagstr)
        except Exception:
            logger.error("Tag {} not found, denied.".format(tagstr))
            return HttpResponse(
                "Tag/Owner not found", status=404, content_type="text/plain"
            )
        try:
            tag.last_used = timezone.now()
            tag.save()
        except Exception as e:
            logger.error(
                "Unexpected error when recording tag use on {}: {}".format(tag, e)
            )

        kwargs["tag"] = tag
        return function(request, *args, **kwargs)

    return wrap


@csrf_exempt
@superuser_or_bearer_required
@checktag
def api_getok_by_node(request, node=None, tag=None):
    try:
        machines = Machine.objects.filter(node_name=node)
    except ObjectDoesNotExist:
        logger.error("Node not found, denied.")
        return HttpResponse("Node not found", status=404, content_type="text/plain")
    if not machines:
        return HttpResponse(
            "Node does not have any machines connecte to it",
            status=404,
            content_type="text/plain",
        )
    out = {}
    for machine in machines:
        r = get_perms(tag, machine)
        if r:
            out[machine.node_machine_name] = r

    return JsonResponse(out)


@csrf_exempt
@is_paired_terminal
# Note: we are not checking if this terminal is actually associated
#       with this node or machine. I.e any valid terminal can ask
#       anything about the others. We may not want that in the future.
def api_gettags4node(request, terminal=None, node=None):
    if not node:
        logger.error("No node, denied.")
        return HttpResponse("No node", status=404, content_type="text/plain")
    try:
        machines = Machine.objects.filter(node_name=node)
    except ObjectDoesNotExist:
        logger.error("Node not found, denied.")
        return HttpResponse("Node not found", status=404, content_type="text/plain")
    if not machines:
        return HttpResponse(
            "Node does not have any machines connecte to it",
            status=404,
            content_type="text/plain",
        )
    out = {}
    for user in User.objects.filter(is_active=True):
        for machine in machines:
            out[machine.name] = []
            if machine.canOperate(user):
                for tag in Tag.objects.filter(owner=user):
                    out[machine.name].append({"tag": tag.tag, "name": str(tag.owner)})

    return JsonResponse(out)


# Note: we are not checking if this terminal is actually associated
#       with this node or machine. I.e any valid terminal can ask
#       anything about the others. We may not want that in the future.
#
def api_gettags4machine(request, terminal=None, machine=None):
    try:
        machine = Machine.objects.get(name=machine)
    except ObjectDoesNotExist:
        logger.error(f"Machine {machine} not found, denied.")
        return HttpResponse("Machine not found", status=404, content_type="text/plain")

    out = []

    for user in User.objects.all():
        (needs, has) = machine.useState(user)
        xs = useNeedsToStateStr(needs, has)
        for tag in Tag.objects.filter(owner=user):
            out.append(
                {
                    "tag": tag.tag,
                    "name": str(tag.owner),
                    "needs": needs,
                    "has": has,
                    "resukt": has & needs == needs,
                    "xs": xs,
                }
            )
    return out


@csrf_exempt
@is_paired_terminal
def api_gettags4machineJSON(request, terminal=None, machine=None):
    out = api_gettags4machine(request, terminal, machine)
    return JsonResponse(out, safe=False)


@csrf_exempt
@is_paired_terminal
def api_gettags4machineCSV(request, terminal=None, machine=None):
    outstr = []
    for e in api_gettags4machine(request, terminal, machine):
        outstr.append(f"{e['tag']},{e['needs']},{e['has']},{e['name']}")

    # We sort; on ascii of the tag - to make a bin-search possible on the client.
    #
    outstr.sort()

    return HttpResponse("\n".join(outstr), status=200, content_type="text/plain")


@csrf_exempt
@superuser_or_bearer_required
@checktag
def api_getok(request, machine=None, tag=None):
    try:
        machine = Machine.objects.get(node_machine_name=machine)
    except ObjectDoesNotExist:
        logger.error("Machine '{}' not found, denied.".format(machine))
        return HttpResponse("Machine not found", status=404, content_type="text/plain")
    try:
        r = RecentUse(user=tag.owner, machine=machine)
        r.save()
    except Exception as e:
        logger.error(
            "Unexpected error when recording machine use of {} by {}: {}".format(
                machine, tag.owner, e
            )
        )
    return JsonResponse(get_perms(tag, machine))


@csrf_exempt
def api_getchangecounter(request):
    c = change_tracker_counter()
    if c is None:
        return HttpResponse("Counter not found", status=500, content_type="text/plain")

    secs = int((c.changed.replace(tzinfo=None) - EPOCH).total_seconds())

    return HttpResponse(
        f"{c.count},{secs}\t# Last change: {c.changed}",
        status=200,
        content_type="text/plain",
    )
