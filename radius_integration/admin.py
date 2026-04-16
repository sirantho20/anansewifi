from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import RadAcct, RadCheck, RadReply


@admin.register(RadCheck)
class RadCheckAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("username", "attribute", "value")
    search_fields = ("username", "attribute", "value")


@admin.register(RadReply)
class RadReplyAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("username", "attribute", "value")
    search_fields = ("username", "attribute", "value")


@admin.register(RadAcct)
class RadAcctAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("username", "acctsessionid", "acctstarttime", "acctstoptime", "acctinputoctets", "acctoutputoctets")
    search_fields = ("username", "acctsessionid", "acctuniqueid", "callingstationid")
