import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from djproxy.views import HttpProxy
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


class NodeRedProxy(HttpProxy):
    base_url = settings.NODERED_URL
    reverse_urls = [
        (r"^nodered/(?P<url>.*)$", settings.NODERED_URL),
        (r"^nodered/dashboard/(?P<url>.*)$", settings.NODERED_URL),
    ]

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        #  Using rest auth outside of the rest framework requires a manual check
        try:
            if not request.user.is_authenticated:
                if not request.user.groups.filter(
                    name=settings.NODERED_ADMIN_GROUP
                ).exists():
                    logger.warning("User is not privileged to access nodered")
                    raise ObjectDoesNotExist()
            elif request.user.is_superuser:
                pass
            elif request.user.groups.filter(
                name=settings.NODERED_ADMIN_GROUP
            ).exists():
                pass
            else:
                logger.warning("User is not logged in and cannot access nodered")
                raise ObjectDoesNotExist()

            return super().dispatch(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return redirect("overview")

@login_required
def NoderedLiveDataAndSensorsView(request):
    node_red_available = True
    context = {
        "node_red_available": node_red_available,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, 'nodered_live_data_and_sensors.html', context)

@login_required
def NoderedSpaceClimateView(request):
    node_red_available = True
    context = {
        "node_red_available": node_red_available,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, 'nodered_space_climate.html', context)