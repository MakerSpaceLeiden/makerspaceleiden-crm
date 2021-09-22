from django.urls import path
from django.urls import path, register_converter

from . import views
from makerspaceleiden import converters

register_converter(converters.FloatUrlParameterConverter, 'float')


urlpatterns = [
    path('', views.index, name='balances'),

    path('show/<int:pk>', views.show, name='transactions'),
    path('invoice/<int:pk>', views.invoice, name='invoice'),
    path('deposit/<int:pk>', views.deposit, name='deposit'),
    path('pay', views.pay, name='pay'),
]
