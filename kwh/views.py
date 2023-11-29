import logging
import os
import re

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse

logger = logging.getLogger(__name__)

WWWROOT = "/var/www/mrtg"


@login_required
def kwh_proxy(request, path):
    if path == "":
        path = "index.html"
    path = "/" + path

    # Curtail slightly what we're allowed to show. The concern here is things like .. and other directory breakouts.
    # So we try to insist on some fairly controlled format of [dir]/name.ext.
    #
    if re.compile(r"^[\w/]*/[-\w]+\.\w+$").match(path):
        file = WWWROOT + path
        if os.path.isfile(file) and not os.path.islink(file):
            return FileResponse(open(WWWROOT + path, "rb"))

    logger.error("Rejecting '/crm/kwh/{}'.".format(path))
    return HttpResponse("XS denied", status=403, content_type="text/plain")
