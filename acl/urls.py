from django.urls import path
from . import views

urlpatterns = [
    path('overview/<int:member_id>', views.member_overview, name='overview'),
    path('overview/', views.overview, name='overview'),
    path('<int:machine_id>', views.details, name='details'),
    path('', views.index, name='index'),
]

