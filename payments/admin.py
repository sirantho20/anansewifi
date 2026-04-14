from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("customer", "plan", "voucher", "amount", "status", "provider", "provider_reference", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("customer__username", "provider_reference")
