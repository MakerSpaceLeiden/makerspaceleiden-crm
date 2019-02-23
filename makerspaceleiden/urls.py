"""makerspaceleiden URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from qr_code import urls as qr_code_urls


urlpatterns = [
    path('', include('selfservice.urls')),
    path('', include('unknowntags.urls')),
    path('', include('django.contrib.auth.urls')),
    path('members/', include('members.urls')),
    path('servicelog/', include('servicelog.urls')),
    path('mailinglists/', include('mailinglists.urls')),
    path('storage/', include('storage.urls')),
    path('boxes/', include('memberbox.urls')),
    path('acl/', include('acl.urls')),
    path('ufo/', include('ufo.urls')),
    path('admin/', admin.site.urls),
#    url(r'^autocomplete/', include('autocomplete_light.urls')),
    path('qr_code/', include(qr_code_urls, namespace='qr_code')),
]

urlpatterns += static(r'/favicon.ico', document_root='static/favicon.ico')

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
