import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.defaulttags import register

from storage.definitions import STORAGES, parse_box_location

from .forms import MemberboxForm, NewMemberboxForm
from .models import Memberbox

logger = logging.getLogger(__name__)


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)


@login_required
def index(request):
    yours = Memberbox.objects.filter(owner=request.user).order_by("location")

    # Prepare empty data structures with rows and columns
    floating = []
    storages = dict(
        (
            storage_key,
            {
                "description": storage_data["description"],
                "boxes": [
                    [
                        {
                            "location": "{0}{1}{2}".format(
                                storage_key, col + 1, storage_data["num_rows"] - row
                            ),
                            "box": None,
                        }
                        for col in range(storage_data["num_cols"])
                    ]
                    for row in range(storage_data["num_rows"])
                ],
            },
        )
        for storage_key, storage_data in STORAGES.items()
    )
    # The storage in the frontroom is funny - so we cannot really use above.
    # Construct something special here.
    #
    ibl = {}
    for i in range(1, 26):
        loc = "M{:0=2}".format(i)
        ibl[loc] = {"location": loc, "box": None}

    # Fill up data structures; and do a count/owner on the side
    count = {}
    morethanone = {}
    for box in Memberbox.objects.order_by("location"):
        ibl[box.location] = {"location": box.location, "box": box}
        if box.owner.id in count:
            count[box.owner.id] = count[box.owner.id] + 1
            morethanone[box.owner] = count[box.owner.id]
        else:
            count[box.owner.id] = 1
        box_location = parse_box_location(box.location)
        if box_location:
            num_rows = STORAGES[box_location.storage]["num_rows"]
            storages[box_location.storage]["boxes"][num_rows - box_location.row][
                box_location.col - 1
            ] = {"location": box.location, "box": box}
        else:
            floating.append(box)

    # The storage in the frontroom is funny - so we cannot really use
    # above; so we delete it and have some custom code in the
    # template to show this.
    del storages["M"]

    context = {
        "title": "Members boxes",
        "user": request.user,
        "has_permission": request.user.is_authenticated,
        "storages": list(storages.values()),
        "items_by_location": ibl,
        "floating": floating,
        "yours": yours,
        "morethanone": morethanone,
    }

    return render(request, "memberbox/index.html", context)


@login_required
def claim(request, location):
    if request.method == "POST":
        form = NewMemberboxForm(
            request.POST or None, request.FILES, initial={"owner": request.user.id}
        )
        if form.is_valid():
            try:
                form.changeReason = (
                    "Created through the self-service interface by {0}".format(
                        request.user
                    )
                )
                form.save()
                for f in form.fields:
                    form.fields[f].widget.attrs["readonly"] = True
                return redirect("boxes")
            except Exception as e:
                logger.error(
                    "Unexpected error during create of new box : {0}".format(e)
                )
    else:
        form = NewMemberboxForm(
            initial={
                "owner": request.user.id,
                "location": location,
            }
        )

    context = {
        "label": "Describe a new box",
        "action": "Create",
        "title": "Create Memberbox",
        "is_logged_in": request.user.is_authenticated,
        "user": request.user,
        "owner": request.user,
        "form": form,
        "has_permission": request.user.is_authenticated,
        "back": "boxes",
    }
    return render(request, "crud.html", context)


@login_required
def create(request):
    return claim(request, "")


@login_required
def modify(request, pk):
    try:
        box = Memberbox.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return HttpResponse("Box not found", status=404, content_type="text/plain")

    if request.method == "POST":
        form = MemberboxForm(request.POST or None, request.FILES, instance=box)
        if form.is_valid():
            logger.error("saving")
            try:
                box.changeReason = (
                    "Updated through the self-service interface by {0}".format(
                        request.user
                    )
                )
                box.save()
                for f in form.fields:
                    form.fields[f].widget.attrs["readonly"] = True
                return redirect("boxes")

            except Exception as e:
                logger.error("Unexpected error during save of box: {0}".format(e))
    else:
        if not box.owner:
            box.owner = request.user
        form = MemberboxForm(request.POST or None, instance=box)

    context = {
        "label": "Update box location and details",
        "action": "Update",
        "title": "Update box details",
        "is_logged_in": request.user.is_authenticated,
        "user": request.user,
        "owner": box.owner,
        "form": form,
        "item": box,
        "has_permission": request.user.is_authenticated,
        "back": "boxes",
    }

    return render(request, "crud.html", context)


@login_required
def delete(request, pk):
    try:
        box = Memberbox.objects.get(pk=pk)
    except Memberbox.DoesNotExist:
        return HttpResponse("Box not found", status=404, content_type="text/plain")

    if not box.can_delete(request.user):
        return HttpResponse(
            "Eh - not your box/no permission ?!", status=403, content_type="text/plain"
        )

    try:
        box.delete(request.user)
    except Exception as e:
        logger.error("Unexpected error during delete of box: {0}".format(e))
        return HttpResponse("Box fail", status=400, content_type="text/plain")

    return redirect("boxes")
