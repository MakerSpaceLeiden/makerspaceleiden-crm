from django.urls import resolve

def motd_context(request):
    # Get the resolved view name
    resolved_view_name = resolve(request.path_info).view_name
    
    # List of views where motd should be included
    views_with_motd = ['index', 
                         'navpage', 
                         'motd_messages', 
                         'motd_messages_detail',
                         'motd_create',
                         'motd_update',
                         'motd_delete' ]
    
    # Check if the current view is in the list of views with motd
    include_motd = resolved_view_name in views_with_motd
    
    return {'include_motd': include_motd}

