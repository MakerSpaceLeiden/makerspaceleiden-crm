from django.http import HttpResponseRedirect,HttpResponse

from django.core.exceptions import PermissionDenied
from django.conf import settings

from functools import wraps

HEADER='HTTP_X_BEARER'

def superuser_or_bearer_required(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
      if request.user.is_superuser:
            return function(request, *args, **kwargs)

      if (settings.UT_BEARER_SECRET and
          request.META.get(HEADER) and
          request.META.get(HEADER) == settings.UT_BEARER_SECRET):
            # set extra flag to singal this shis non user case? 
            return function(request, *args, **kwargs)

      # Quell some odd 'code 400, message Bad request syntax ('tag=1-2-3-4')'
      request.POST 
      # raise PermissionDenied
      return HttpResponse("XS denied",status=403,content_type="text/plain")
  return wrap
