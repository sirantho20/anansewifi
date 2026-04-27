from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("plans/", views.plans_view, name="plans"),
    path("packages/", views.plans_view, name="packages"),
    path("login/", views.login_view, name="login"),
    path("purchase/start/", views.purchase_start_view, name="purchase-start"),
    path("purchase/callback/", views.purchase_callback_view, name="purchase-callback"),
    path("session/<str:username>/", views.session_status_view, name="session-status"),
]
