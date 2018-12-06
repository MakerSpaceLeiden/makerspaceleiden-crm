from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse

from .models import Entitlement

def index(request):
    lst = Entitlement.objects.order_by('holder__username')
    agg = {}
    perms = {}
    output = ''
    for e in lst:
      if not e.holder.username in agg:
        agg[e.holder.username] = {}
      perms[ e.permit.name ] = 1
      agg[ e.holder.username ][e.permit.name] = 1
    for h in agg.keys():
      output += '<li>'+h+': '+' '.join(agg[h])

    context = {
        'agg': agg,
        'perms': perms,
    }
    return render(request, 'index.html', context)
