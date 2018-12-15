from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, { 'user_pk': None }, name='storage'),
    path('<int:user_pk>', views.index, name='storage'),

    path('add', views.create, name='addstorage'),
    path('modify/<int:pk>', views.modify, name='changestorage'),
    path('delete/<int:pk>', views.delete, name='deletestorage'),

]

