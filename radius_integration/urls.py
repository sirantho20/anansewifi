from django.urls import path

from .views import RadiusAccountingIngestView

app_name = "radius_integration"

urlpatterns = [
    path("accounting/", RadiusAccountingIngestView.as_view(), name="accounting"),
]
