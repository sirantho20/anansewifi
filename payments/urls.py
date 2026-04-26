from django.urls import path

from .api import PurchaseInitializeView, PurchaseVerifyView

urlpatterns = [
    path("initialize/", PurchaseInitializeView.as_view(), name="purchase-initialize"),
    path("verify/", PurchaseVerifyView.as_view(), name="purchase-verify"),
]
