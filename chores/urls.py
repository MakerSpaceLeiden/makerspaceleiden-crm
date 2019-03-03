from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='chores'),
    path('signup/<int:chore_id>/<int:ts>', views.signup, name='signup_chore'),
]

