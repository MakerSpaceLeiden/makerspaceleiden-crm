from django.urls import path
from . import views

urlpatterns = [
    path('<int:machine_id>', views.details, name='details'),
    path('', views.index, name='index'),
]

