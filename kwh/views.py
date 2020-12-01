from django.shortcuts import render,redirect
from django.template import loader
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse

import os, re
import logging
logger = logging.getLogger(__name__)

WWWROOT='/var/www/mrtg'

@login_required
def kwh_proxy(request, path):
    if path == '':
        path = 'index.html'
    path = '/'+path

    # Curtail slightly what we're allowed to show. The concern here is things like .. and other directory breakouts.
    # So we try to insist on some fairly controlled format of [dir]/name.ext.
    #
    if re.compile(r'^[\w/]*/[-\w]+\.\w+$').match(path):
        file = WWWROOT + path
        if os.path.isfile(file) and not os.path.islink(file):
             return FileResponse(open(WWWROOT + path, 'rb'))

    logger.error("Rejecting '/crm/kwh/{}'.".format(path))
    return HttpResponse("XS denied",status=403,content_type="text/plain")

