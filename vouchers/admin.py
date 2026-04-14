from django.contrib import admin

from .models import Voucher, VoucherBatch


@admin.register(VoucherBatch)
class VoucherBatchAdmin(admin.ModelAdmin):
    list_display = ("name", "code_prefix", "plan", "quantity", "expires_at")
    search_fields = ("name", "code_prefix", "plan__name")


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("code", "plan", "status", "redeemed_by", "expires_at", "use_count", "max_uses")
    list_filter = ("status", "plan")
    search_fields = ("code", "redeemed_by__username")
