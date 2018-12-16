from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse

from .models import Entitlement

def index(request):
    lst = Entitlement.objects.order_by('holder__id')
    agg = {}
    perms = {}
    output = ''
    for e in lst:
      if not e.holder.id in agg:
        agg[e.holder.id ] = {}
      perms[ e.permit.name ] = 1
      agg[ e.holder.id ][e.permit.name] = 1
    for h in agg.keys():
      output += '<li>'+h+': '+' '.join(agg[h])

    context = {
        'agg': agg,
        'perms': perms,
    }
    return render(request, 'index.html', context)
