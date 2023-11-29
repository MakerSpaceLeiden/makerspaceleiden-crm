from django.urls import path, register_converter

from makerspaceleiden import converters

from . import views

register_converter(converters.FloatUrlParameterConverter, "float")

urlpatterns = [
    path("", views.index, name="balances"),
    path("show/<int:pk>", views.show, name="transactions"),
    path("show", views.show_mine, name="mytransactions"),
    path("pricelist", views.pricelist, name="pricelist"),
    path("spends", views.spends, name="spends"),
    path("qrcode", views.qrcode, name="qrcode"),
    path("manual_deposit", views.manual_deposit, name="manual_deposit"),
    path("showall", views.showall, name="all_transactiondetail"),
    path("showtx/<int:pk>", views.showtx, name="transactiondetail"),
    path("invoice/<int:src>", views.invoice, name="invoice"),
    path(
        "transfer_to_member/<int:src>",
        views.transfer_to_member,
        name="transfer_to_member",
    ),
    path("transfer/<int:src>/<int:dst>", views.transfer, name="transfer"),
    path("deposit/<int:dst>", views.deposit, name="deposit"),
    path("delete/<int:pk>", views.delete, name="delete"),
    path("cam53upload", views.cam53upload, name="cam53upload"),
    path("cam53process", views.cam53process, name="cam53process"),
    path("unpaired", views.unpaired, name="unpaired"),
    path("pair/<int:pk>", views.pair, name="pair"),
    path("forget/<int:pk>", views.forget, name="forget"),
    # Reimbursement related
    path("reimburse_request", views.reimburseform, name="reimburseform"),
    path("payout_request", views.payoutform, name="payoutform"),
    path("reimburse_queue", views.reimburseque, name="reimburse_queue"),
    # User interface - need to be logged in
    path("pay", views.pay, name="pay"),
    # Essentially the same - but for M2M - with bearer token over
    # localhost allowed to impersonate a known/authenticated user.
    #
    path("api/none", views.api_none, name="api-none"),
    path("api/v1/pay", views.api_pay, name="acl-v1-pay"),
    # Client-cert based auth variation.
    #
    path("api/v2/register", views.api2_register, name="acl-v2-register"),
    path("api/v2/pay", views.api2_pay, name="acl-v1-pay"),
    # Calls with no security (yet)
    path("api/v1/skus", views.api_get_skus, name="acl-v1-get-skus"),
    path("api/v1/sku/<int:sku>", views.api_get_sku, name="acl-v1-get-sku"),
    path("api/v2/skus", views.api_get_skus, name="acl-v1-get-skus"),
    path("api/v2/sku/<int:sku>", views.api_get_sku, name="acl-v1-get-sku"),
]
