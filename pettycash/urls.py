from django.urls import path
from django.urls import path, register_converter

from . import views
from makerspaceleiden import converters

register_converter(converters.FloatUrlParameterConverter, 'float')


urlpatterns = [
    path('', views.index, name='balances'),

    path('show/<int:pk>', views.show, name='transactions'),
    path('showtx/<int:pk>', views.showtx, name='transactiondetail'),
    path('invoice/<int:src>', views.invoice, name='invoice'),
    path('transfer/<int:src>/<int:dst>', views.transfer, name='transfer'),
    path('deposit/<int:dst>', views.deposit, name='deposit'),
    path('pay', views.pay, name='pay'),
]
