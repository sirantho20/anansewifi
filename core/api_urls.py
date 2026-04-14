from django.urls import include, path
from rest_framework.routers import DefaultRouter

from customers.api import CustomerViewSet
from dashboard.api import DashboardSummaryView
from network.api import NASDeviceViewSet
from plans.api import PlanViewSet
from sessions.api import SessionViewSet
from vouchers.api import VoucherViewSet

router = DefaultRouter()
router.register("plans", PlanViewSet, basename="plan")
router.register("customers", CustomerViewSet, basename="customer")
router.register("vouchers", VoucherViewSet, basename="voucher")
router.register("sessions", SessionViewSet, basename="session")
router.register("nas-devices", NASDeviceViewSet, basename="nas-device")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("payments/", include("payments.urls")),
    path("radius/", include("radius_integration.urls")),
]
