from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("sessions/", views.active_sessions, name="active-sessions"),
    path("auth-issues/", views.auth_issues, name="auth-issues"),
]
