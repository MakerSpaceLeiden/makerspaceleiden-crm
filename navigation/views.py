from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def NavpageView(request): 
    context = {
        "title": "Navigation",
        "has_permission": request.user.is_authenticated,
    }
    return render(request, 'navigation/navpage.html', context)
