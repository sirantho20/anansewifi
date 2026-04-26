from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("customer", "plan", "voucher", "amount", "status", "provider", "provider_reference", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("customer__username", "provider_reference")
    autocomplete_fields = ("customer", "plan", "voucher")
