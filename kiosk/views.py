from django.http import HttpResponse
from django.shortcuts import render

from makerspaceleiden.decorators import user_or_kiosk_required
from selfservice.aggregator_adapter import get_aggregator_adapter


@user_or_kiosk_required
def kiosk(request):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )
    context = aggregator_adapter.fetch_state_space()
    context["user"] = None

    return render(request, "kiosk.html", context)
