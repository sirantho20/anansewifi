from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import Voucher, VoucherBatch


@admin.register(VoucherBatch)
class VoucherBatchAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code_prefix", "plan", "quantity", "expires_at")
    search_fields = ("name", "code_prefix", "plan__name")
    autocomplete_fields = ("plan",)


@admin.register(Voucher)
class VoucherAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("code", "plan", "status", "redeemed_by", "expires_at", "use_count", "max_uses")
    list_filter = ("status", "plan")
    search_fields = ("code", "redeemed_by__username")
    autocomplete_fields = ("plan", "batch", "redeemed_by")
