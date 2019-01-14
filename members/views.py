from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from acl.models import Entitlement

@login_required
def index(request):
    lst = Entitlement.objects.order_by('holder__id')
    agg = {}
    perms = {}
    output = ''
    for e in lst:
      if not e.holder in agg:
        agg[e.holder ] = {}
      perms[ e.permit.name ] = 1
      agg[ e.holder ][e.permit.name] = 1

    context = {
        'agg': agg,
        'perms': perms,
    }
    return render(request, 'members/index.html', context)
