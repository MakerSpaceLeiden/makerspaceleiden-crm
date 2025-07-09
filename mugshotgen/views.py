import logging
import sys
import uuid

from robohash import Robohash

from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)

def index(request,pk = None):
    if not pk:
       pk = uuid(16)

    rh = Robohash(str(pk))
    rh.assemble(roboset=settings.ROBOHASH_SET, format='png', color=settings.ROBOHASH_COLOUR, bgset=None)

    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = 'inline; filename="mugshot-{}.png"'.format(pk)

    rh.img.save(response, "PNG")
    return response


