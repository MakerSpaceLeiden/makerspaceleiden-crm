from django import template
from motd.models import Motd
from django.db.models import Q
from datetime import datetime, date

register = template.Library()

@register.inclusion_tag('motd/motd.html')
def render_motd():
    
    current_date = date.today()
    current_time = datetime.now().time()

    motd_items = Motd.objects.filter(
       Q(startdate__lte=current_date),
       Q(enddate__gte=current_date),
       (Q(enddate__gt=current_date) | (Q(enddate=current_date) & Q(endtime__gte=current_time)))
       ).order_by('-startdate')[:20]

    return {'motd_items': motd_items}

