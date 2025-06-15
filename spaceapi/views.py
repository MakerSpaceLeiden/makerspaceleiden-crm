import datetime
import logging

from dateutil import parser
from django.http import HttpResponse
from django.shortcuts import redirect, render

from selfservice.aggregator_adapter import get_aggregator_adapter

logger = logging.getLogger(__name__)


def redir(request):
    # We currently only support version 0.13 - so explictly redirect.
    return redirect("spaceapi013")


# No access restrictions
def index(request):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    try:
        state = aggregator_adapter.fetch_state_space()
    except Exception as e:
        return HttpResponse(
            "Agregator unhappy", status=500, content_type="text/plain"
        )

    context = {"open": "false"}

    if state["lights_on"]:
        context = {"open": "true"}  # must be lowercase

    for e in state["machines"]:
        m = e["machine"]
        if "light" in m["name"].lower() and "state" in m and "on" in m["state"].lower():
            context = {"open": "true"}  # must be lowercase

    if bool(state["users_in_space"]):
        context = {"open": "true"}  # must be lowercase

    lst = datetime.datetime(1970, 1, 1)
    for user in state["users_in_space"]:
        ulst = parser.parse(user["ts_checkin"])
        if ulst > lst:
            lst = ulst
    context["lastSinceEpoch"] = lst.strftime("%s")

    resp = render(request, "spaceapi.json", context)

    # Add headers to make validator happyL
    #   https://validator.spaceapi.io/ui/?url=https://makerspaceleiden.nl/crm/spaceapi/0.13
    #
    resp["Access-Control-Allow-Origin"] = "*"
    resp["Access-Control-Allow-Headers"] = "*"
    resp["content-type"] = "application/json"

    return resp
