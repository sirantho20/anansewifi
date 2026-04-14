from django.contrib import admin

from .models import RadAcct, RadCheck, RadReply


@admin.register(RadCheck)
class RadCheckAdmin(admin.ModelAdmin):
    list_display = ("username", "attribute", "value")
    search_fields = ("username", "attribute", "value")


@admin.register(RadReply)
class RadReplyAdmin(admin.ModelAdmin):
    list_display = ("username", "attribute", "value")
    search_fields = ("username", "attribute", "value")


@admin.register(RadAcct)
class RadAcctAdmin(admin.ModelAdmin):
    list_display = ("username", "acctsessionid", "acctstarttime", "acctstoptime", "acctinputoctets", "acctoutputoctets")
    search_fields = ("username", "acctsessionid", "acctuniqueid", "callingstationid")
