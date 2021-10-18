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
    path('delete/<int:pk>', views.delete, name='delete'),

    path('cam53upload', views.cam53upload, name='cam53upload'),
    path('cam53process', views.cam53process, name='cam53process'),

    path('unpaired', views.unpaired, name='unpaired'),
    path('pair/<int:pk>', views.pair, name='pair'),

    # User interface - need to be logged in
    path('pay', views.pay, name='pay'),

    # Essentially the same - but for M2M - with bearer token over
    # localhost allowed to impersonate a known/authenticated user.
    #
    path('api/v1/pay', views.api_pay, name='acl-v1-pay'),
    path('api/v1/skus', views.api_get_skus, name='acl-v1-get-skus'),
    path('api/v1/sku/<int:sku>', views.api_get_sku, name='acl-v1-get-sku'),
    path('api/v1/register', views.api_register, name='acl-v1-register'),
]
