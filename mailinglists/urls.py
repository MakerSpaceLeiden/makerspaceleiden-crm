from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('mailinglists_edit/<int:user_id>', views.mailinglists_edit , name='mailinglists_edit'),
    path('mailinglists_edit', views.mailinglists_edit , name='mailinglists_edit'),

    path('archive/<str:mlist>/<str:yearmonth>/<str:order>.html', views.mailinglists_archive, name='mailinglists_archive'),
    path('archive/<str:mlist>/<str:yearmonth>.<str:zip>', views.mailinglists_archive, name='mailinglists_archive'),
    path('archive/<str:mlist>/<str:yearmonth>/', views.mailinglists_archive, name='mailinglists_archive'),
    path('archive/<str:mlist>/', views.mailinglists_archive, name='mailinglists_archive'),
    path('archive', views.mailinglists_archives, name='mailinglists_archives'),
]
