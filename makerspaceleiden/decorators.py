from django.http import HttpResponseRedirect,HttpResponse

from django.core.exceptions import PermissionDenied
from django.conf import settings

from functools import wraps
import re

HEADER='HTTP_X_BEARER'
MODERN_HEADER='HTTP_AUTHORIZATION'

import logging
logger = logging.getLogger(__name__)

def superuser_or_bearer_required(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
      if request.user:
          if type(request.user).__name__ == 'User':
              if request.user.is_privileged:
                  return function(request, *args, **kwargs)

      if hasattr(settings, 'UT_BEARER_SECRET'):
          secret = None
          # Pendantic header
          if request.META.get(HEADER):
              secret = request.META.get(HEADER)

          # Also accept a modern RFC 6750 style header.
          elif request.META.get(MODERN_HEADER):
              match = re.search(r'\bbearer\s+(\S+)', request.META.get(MODERN_HEADER), re.IGNORECASE)
              if match:
                  secret = match.group(1)

          for bs in settings.UT_BEARER_SECRET.split():
              if secret == bs:
                  return function(request, *args, **kwargs)

      # Quell some odd 'code 400, message Bad request syntax ('tag=1-2-3-4')'
      request.POST 

      # raise PermissionDenied
      return HttpResponse("XS denied",status=403,content_type="text/plain")
  return wrap

def user_or_kiosk_required(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
      if request.user and type(request.user).__name__ == 'User':
           return function(request, *args, **kwargs)

      x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
      if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
      else:
        ip = request.META.get('REMOTE_ADDR')

      if ip == '127.0.0.1':
           return function(request, *args, **kwargs)

      # Quell some odd 'code 400, message Bad request syntax ('tag=1-2-3-4')'
      request.POST 

      # raise PermissionDenied
      return HttpResponse("XS denied",status=403,content_type="text/plain")
  return wrap


