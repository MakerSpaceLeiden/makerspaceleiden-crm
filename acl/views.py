import hashlib
import logging
import re
import secrets
from functools import wraps

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from dateutil.tz.tz import EPOCH
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Upper
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
    machines = (
        Machine.objects.filter(do_not_show=False)
        .annotate(upper_name=Upper("name"))
        .order_by("upper_name")
    )
    members = User.objects.all().filter(is_active=True).order_by("first_name")

    machines_category = {
        "machines": machines.filter(category="machine").order_by("upper_name"),
        "general_equipment": machines.filter(category="general_equipment").order_by(
            "upper_name"
        ),
        "lights": machines.filter(category="lights").order_by("upper_name"),
    }

    context = {
        "members": members,
        "machines_category": machines_category,
        "has_permission": request.user.is_authenticated,
        "title": "Machines",
    }
    return render(request, "acl/machines.html", context)


@login_required
def machine_overview(request, machine_id=None):
    instructors = []
    used = []
    machines = Machine.objects.filter(do_not_show=False).order_by("name")
    if machine_id:
        try:
            machines = Machine.objects.filter(pk=machine_id)
        except ObjectDoesNotExist:
            return HttpResponse(
                "Machine not found", status=404, content_type="text/plain"
            )
        machine = machines.first()
        print(machine)
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

    machines = (
        Machine.objects.filter(do_not_show=False)
        .annotate(upper_name=Upper("name"))
        .order_by("upper_name")
    )
    boxes = Memberbox.objects.all().filter(owner=member)
    storage = Storage.objects.all().filter(owner=member)
    subscriptions = Subscription.objects.all().filter(member=member)

    # Create lst dictionary with machine details
    lst = {}
    for mchn in machines:
        details = matrix_mm(mchn, member)
        details["name"] = mchn.name  # Add name here
        details["category"] = mchn.get_category_display()
        details["path"] = mchn.path()
        lst[mchn.name] = details

    # Categorize and sort machines
    categorized_machines = {"Machine": [], "General equipment": [], "Lights": []}

    for name, details in lst.items():
        human_readable_category = details.get("category", "Uncategorized")
        if human_readable_category in categorized_machines:
            categorized_machines[human_readable_category].append(details)

    # Sort each category's machines by name
    for category in categorized_machines:
        categorized_machines[category] = sorted(
            categorized_machines[category], key=lambda x: x["name"].upper()
        )

    # Fetch entitlements
    normal_permits = {m.requires_permit: True for m in machines if m.requires_permit}
    specials = [
        e
        for e in Entitlement.objects.filter(holder=member)
        if e.permit not in normal_permits
    ]

    specials = []
    for e in Entitlement.objects.all().filter(holder=member):
        if e.permit not in normal_permits:
            specials.append(e)

    balance = 0
    try:
        balance = PettycashBalanceCache.objects.get(owner=member)

    except ObjectDoesNotExist:
        pass

    context = {
        "title": member.first_name + " " + member.last_name,
        "member": member,
        "machines": categorized_machines,
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
            tag.save(update_fields=["last_used"])
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


@csrf_exempt
@is_paired_terminal
def api_gettags4machine(request, terminal=None, machine=None):
    try:
        machine = Machine.objects.get(name=machine)
    except ObjectDoesNotExist:
        logger.error(f"get4machine: Machine '{machine}' not found, denied.")
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
                    "result": has & needs == needs,
                    "xs": xs,
                }
            )
    return out


# Note: we are not checking if this terminal is actually associated
#       with this node or machine. I.e any valid terminal can ask
#       anything about the others. We may not want that in the future.
#
@csrf_exempt
@csrf_exempt
@is_paired_terminal
def api_gettags4machineJSON(request, terminal=None, machine=None):
    out = api_gettags4machine(request, terminal, machine)
    if isinstance(out, HttpResponse):
        return out

    # Sort on ASCII of the tag -- to make a bin-search possible on the client.
    return JsonResponse(sorted(out, key=lambda d: d["tag"]), safe=False)


# Note: we are not checking if this terminal is actually associated
#       with this node or machine. I.e any valid terminal can ask
#       anything about the others. We may not want that in the future.
#
@csrf_exempt
@csrf_exempt
@is_paired_terminal
def api_gettags4machineCSV(request, terminal=None, machine=None):
    out = api_gettags4machine(request, terminal, machine)
    if isinstance(out, HttpResponse):
        return out

    outstr = []
    for e in out:
        outstr.append(f"{e['tag']},{e['needs']},{e['has']},{e['name']}")

    # We sort; on ascii of the tag -- to make a bin-search possible on the client.
    #
    outstr.sort()

    return HttpResponse("\n".join(outstr), status=200, content_type="text/plain")


def byte_xor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])


def nameShorten(name, maxlen=10):
    if len(name) <= maxlen:
        return name
    # parts = name.split(' ')
    parts = re.split("[^a-zA-Z]", name)
    name = parts.pop(0)
    for i in parts:
        if len(name) > maxlen - 1:
            return name[0:maxlen]
        if len(name) + len(i) > maxlen:
            i = i[0]
        name += i
    return name


# Note: we are not checking if this terminal is actually associated
#       with this node or machine. I.e any valid terminal can ask
#       anything about the others. We may not want that in the future.
#
# Compact/IoT oriented version of the tag/acl package.
#
# idx len
#  0     4			MSL1 -- version of this file
#  4     4                       Unique Identiifier
#  8     4			timestamp, unix epoch, in seconds, network (big endian) order
#  12    4			LT Length of the tag section, network order
#  16    4			LM Length of the members section, network order
#  20   32			salt for the tags
#  52   32                      salt for the keys
#  84   32 			IV seed for the iv used in encrypting the member names
# 116   LT			tag section; N entries of XX bytes = LT long
#       68	0   32       	salted tag; sha256( salt || tag-as-ascii)
# 		32  32		decryption key user name; xor(salted tag, sha255( tag || key salt)
#               64  04          Index into the member section, 4 bytes, network order
# 116+LT	LM		member section
#      *        0    1 		has
#               1    1          needs
#               2    1          LES: Length encrypted section
#               3    LES	AES-CBC, padded, ecrypted with the first 16 bytes of
#                               sha256( iv || Index) as the iv and key from tag section.
#
# 116+LT+LM                      EOF
#
# MSL2 -- same as above; but the AES block no longer just contains
# the name of the user; but also their unqiue user ID (for API
# purposes) and their first/last name separate.
#
def tags4machineBIN(terminal=None, machine=None, v2=False):
    try:
        machine = Machine.objects.get(node_machine_name=machine)
        ctc = change_tracker_counter()
    except ObjectDoesNotExist:
        logger.error(
            f"BIN request for an unknown machine: {machine} (node-machine-name)"
        )
        raise ObjectDoesNotExist

    tl = []
    iv = secrets.token_bytes(32)
    salt = secrets.token_bytes(32)
    keysalt = secrets.token_bytes(32)

    udb = b""
    udx = 0
    for user in User.objects.all().filter():
        (needs, has) = machine.useState(user)

        key = secrets.token_bytes(32)
        uiv = hashlib.sha256(iv + udx.to_bytes(4, "big")).digest()[0:16]

        name = user.name()
        block = b""
        if v2:
            # The identifier is treated like an opaque string; i.e. it may well be a UUID, etc.
            block += str(user.id).encode("ASCII") + b"\0"
            # shorter, simplified name for very small display purposes.
            block += (
                nameShorten(user.first_name.encode("ASCII", errors="ignore"), 12)
                + b"\0"
            )
        block += name.encode("utf-8")

        # This is a weak AES mode; with no protection against
        # bit flipping, clear text, etc. However it is integrity
        # protected during transport; and only protects a name
        # that can be learned through different routes. So we
        # see this as a reasonable trade off; as it saves
        # 32/64 bytes for a nonce/token; e.g. when using a
        # modern mode such as CGM (which # is not supported yet
        # by ESP32 anyway).
        #
        clr = pad(block, AES.block_size)
        if len(clr) > 128:
            raise Exception("information block too large")

        enc = AES.new(key, AES.MODE_CBC, iv=uiv).encrypt(clr)

        udb += has.to_bytes(1, "big")  # only one byte
        udb += needs.to_bytes(1, "big")  # only one byte
        udb += len(enc).to_bytes(1, "big")
        udb += enc

        for tag in Tag.objects.filter(owner=user):
            saltedtag = hashlib.sha256(salt + tag.tag.encode("utf-8")).digest()
            saltedkey = hashlib.sha256(tag.tag.encode("utf-8") + keysalt).digest()
            tagkey = byte_xor(key, saltedkey)

            # Special test tag - used for e2e tests.
            if tag.tag == "1-2-5":
                logger.debug(
                    f"Tag: {tag.tag} -- {name}\n\tSalt={salt.hex()}\n\tsaltedtag={saltedtag.hex()}\n\tsaltedkey={saltedkey.hex()}\n\ttagkey={tagkey.hex()}\n\tI={udx}\n\tH,N,len={has},{needs},{len(enc)}\n\tkey={key.hex()}\n\tuiv={uiv.hex()}\n\tclr={clr.hex()}\n\tenc={enc.hex()}\n"
                )

            tl.append(
                {
                    "saltedtag": saltedtag,
                    "tagkey": tagkey,
                    "udx": udx,
                }
            )
        udx = len(udb)

    # Do a sort on the salted tag hashes; to allow for a binary
    # search at the client.
    #
    tl = sorted(tl, key=lambda d: d["saltedtag"])
    tlb = b""
    for e in tl:
        tlb += e["saltedtag"]
        tlb += e["tagkey"]
        tlb += e["udx"].to_bytes(4, "big")

    hdr = b""
    if v2:
        hdr += "MSL2".encode("ASCII")
    else:
        hdr += "MSL1".encode("ASCII")
    hdr += ctc.count.to_bytes(
        4, "big"
    )  # byte order not strictly needed - opaque 4 bytes.
    hdr += int((ctc.changed.replace(tzinfo=None) - EPOCH).total_seconds()).to_bytes(
        4, "big"
    )
    hdr += len(tlb).to_bytes(4, "big")
    hdr += len(udb).to_bytes(4, "big")
    hdr += salt
    hdr += keysalt
    hdr += iv

    logger.debug(f"Header {len(hdr)} Tags: {len(tlb)} Users: {len(udb)}\n")
    return hdr + tlb + udb


@csrf_exempt
@is_paired_terminal
def api_gettags4machineBIN(request, terminal=None, machine=None):
    try:
        out = tags4machineBIN(terminal, machine)
    except ObjectDoesNotExist:
        logger.error(f"getBIN: Machine '{machine}' not found, denied.")
        return HttpResponse("Machine not found", status=404, content_type="text/plain")
    except Exception as e:
        logger.error(f"api_gettags4machineBIN::Exception: {e}")
        return HttpResponse("Internal Error", status=500, content_type="text/plain")

    return HttpResponse(out, status=200, content_type="application/octet-stream")


@csrf_exempt
@is_paired_terminal
def api2_gettags4machineBIN(request, terminal=None, machine=None):
    try:
        out = tags4machineBIN(terminal, machine, v2=True)
    except ObjectDoesNotExist:
        logger.error(f"getBIN: Machine '{machine}' not found, denied.")
        return HttpResponse("Machine not found", status=404, content_type="text/plain")
    except Exception as e:
        logger.error(f"Exception: api2_gettags4machineBIN {e}")
        return HttpResponse("Internal Error", status=500, content_type="text/plain")

    return HttpResponse(out, status=200, content_type="application/octet-stream")


@csrf_exempt
@superuser_or_bearer_required
@checktag
def api_getok(request, machine=None, tag=None):
    try:
        machine = Machine.objects.get(node_machine_name=machine)
    except ObjectDoesNotExist:
        logger.error("getok: Machine '{}' not found, denied.".format(machine))
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


@csrf_exempt
def api_getchangecounterJSON(request):
    c = change_tracker_counter()
    if c is None:
        return HttpResponse("Counter not found", status=500, content_type="text/plain")

    secs = int((c.changed.replace(tzinfo=None) - EPOCH).total_seconds())

    return JsonResponse({"count": c.count, "secondsSinceEpoch": secs}, safe=False)
