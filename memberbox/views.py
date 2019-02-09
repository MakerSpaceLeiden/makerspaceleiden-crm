from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist

from .models import Memberbox
from .forms import MemberboxForm, NewMemberboxForm
from storage.definitions import parse_box_location, STORAGES

import logging
logger = logging.getLogger(__name__)


@login_required
def index(request):
    yours = Memberbox.objects.filter(owner = request.user).order_by('location')

    # Prepare empty data structures with rows and columns
    floating = []
    storages = dict((storage_key, {
        'description': storage_data['description'],
        'boxes': [[{'location': '{0}{1}{2}'.format(storage_key, col+1, storage_data['num_rows']-row), 'box': None} for col in range(storage_data['num_cols'])] for row in range(storage_data['num_rows'])],
    }) for storage_key, storage_data in STORAGES.items())

    # Fill up data structures
    for box in Memberbox.objects.order_by('location'):
        box_location = parse_box_location(box.location)
        if box_location:
            num_rows = STORAGES[box_location.storage]['num_rows']
            storages[box_location.storage]['boxes'][num_rows-box_location.row][box_location.col-1] = {'location': box.location, 'box': box}
        else:
            floating.append(box)

    context = {
        'title': 'Storage',
        'user' : request.user,
        'has_permission': request.user.is_authenticated,
        'storages': list(storages.values()),
        'floating': floating,
        'yours': yours,
    }

    return render(request, 'memberbox/index.html', context)

@login_required
def create(request):
    if request.method == "POST":
      form = NewMemberboxForm(request.POST or None, request.FILES, initial = { 'owner': request.user.id })
      if form.is_valid():
       try:
           form.changeReason = 'Created through the self-service interface by {0}'.format(request.user)
           form.save()
           for f in form.fields:
             form.fields[f].widget.attrs['readonly'] = True
           return redirect('boxes')
       except Exception as e:
         logger.error("Unexpected error during create of new box : {0}".format(e))
    else:
      form = NewMemberboxForm(initial = { 'owner': request.user.id })

    context = {
        'label': 'Describe a new box',
        'action': 'Create',
        'title': 'Create Memberbox',
        'is_logged_in': request.user.is_authenticated,
        'user' : request.user,
        'owner' : request.user,
        'form':  form,
    }
    return render(request, 'memberbox/crud.html', context)

@login_required
def modify(request,pk):
    try:
         box = Memberbox.objects.get(pk=pk)
    except ObjectDoesNotExist:
         return HttpResponse("Box not found",status=404,content_type="text/plain")

    if request.method == "POST":
     form = MemberboxForm(request.POST or None, request.FILES, instance = box)
     if form.is_valid():
       logger.error("saving")
       try:
           box.changeReason = 'Updated through the self-service interface by {0}'.format(request.user)
           box.save()
           for f in form.fields:
             form.fields[f].widget.attrs['readonly'] = True
           return redirect('boxes')

       except Exception as e:
         logger.error("Unexpected error during save of box: {0}".format(e))
    else:
       if not box.owner:
           box.owner = request.user
       form = MemberboxForm(request.POST or None, instance = box)

    context = {
        'label': 'Update box location and details',
        'action': 'Update',
        'title': 'Update box details',
        'is_logged_in': request.user.is_authenticated,
        'user' : request.user,
        'owner' : box.owner,
        'form':  form,
        'box': box,
    }

    return render(request, 'memberbox/crud.html', context)

@login_required
def delete(request,pk):
    try:
         box = Memberbox.objects.get(pk=pk)
    except Memberbox.DoesNotExist:
         return HttpResponse("Box not found",status=404,content_type="text/plain")


    if box.owner != request.user:
         return HttpResponse("Eh - not your box ?!",status=403,content_type="text/plain")

    try:
       box.delete()
    except Exception as e:
         logger.error("Unexpected error during delete of box: {0}".format(e))
         return HttpResponse("Box fail",status=400,content_type="text/plain")

    return redirect('boxes')
