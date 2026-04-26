from django.db import models


class RadCheck(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=":=")
    value = models.CharField(max_length=253)

    class Meta:
        db_table = "radcheck"
        ordering = ["username", "attribute"]

    def __str__(self) -> str:
        return f"{self.username}:{self.attribute}"


class RadReply(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=":=")
    value = models.CharField(max_length=253)

    class Meta:
        db_table = "radreply"
        ordering = ["username", "attribute"]

    def __str__(self) -> str:
        return f"{self.username}:{self.attribute}"


class RadUserGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, db_index=True)
    groupname = models.CharField(max_length=64)
    priority = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "radusergroup"
        ordering = ["username", "priority"]


class RadGroupCheck(models.Model):
    id = models.BigAutoField(primary_key=True)
    groupname = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=":=")
    value = models.CharField(max_length=253)

    class Meta:
        db_table = "radgroupcheck"
        ordering = ["groupname", "attribute"]


class RadGroupReply(models.Model):
    id = models.BigAutoField(primary_key=True)
    groupname = models.CharField(max_length=64, db_index=True)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=":=")
    value = models.CharField(max_length=253)

    class Meta:
        db_table = "radgroupreply"
        ordering = ["groupname", "attribute"]


class RadAcct(models.Model):
    radacctid = models.BigAutoField(primary_key=True)
    acctsessionid = models.CharField(max_length=64)
    acctuniqueid = models.CharField(max_length=32, unique=True)
    username = models.CharField(max_length=64, db_index=True)
    realm = models.CharField(max_length=64, blank=True, null=True)
    nasipaddress = models.GenericIPAddressField(null=True, blank=True, protocol="IPv4")
    nasportid = models.CharField(max_length=15, blank=True, null=True)
    nasporttype = models.CharField(max_length=32, blank=True)
    acctstarttime = models.DateTimeField(null=True, blank=True)
    acctstartdelay = models.PositiveIntegerField(null=True, blank=True)
    acctupdatetime = models.DateTimeField(null=True, blank=True)
    acctstoptime = models.DateTimeField(null=True, blank=True)
    acctstopdelay = models.PositiveIntegerField(null=True, blank=True)
    acctinterval = models.PositiveIntegerField(null=True, blank=True)
    acctsessiontime = models.PositiveIntegerField(null=True, blank=True)
    acctauthentic = models.CharField(max_length=32, blank=True)
    connectinfo_start = models.CharField(max_length=50, blank=True)
    connectinfo_stop = models.CharField(max_length=50, blank=True, null=True)
    acctinputoctets = models.BigIntegerField(default=0)
    acctoutputoctets = models.BigIntegerField(default=0)
    calledstationid = models.CharField(max_length=50, blank=True)
    callingstationid = models.CharField(max_length=50, blank=True)
    acctterminatecause = models.CharField(max_length=32, blank=True, null=True)
    servicetype = models.CharField(max_length=32, blank=True)
    framedprotocol = models.CharField(max_length=32, blank=True)
    framedipaddress = models.GenericIPAddressField(null=True, blank=True, protocol="IPv4")
    framedipv6address = models.GenericIPAddressField(null=True, blank=True)
    framedipv6prefix = models.CharField(max_length=45, blank=True, null=True)
    framedinterfaceid = models.CharField(max_length=44, blank=True, null=True)
    delegatedipv6prefix = models.CharField(max_length=45, blank=True, null=True)
    class_attribute = models.CharField(max_length=64, blank=True, null=True, db_column="class")
    xascendsessionsvrkey = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = "radacct"
        ordering = ["-radacctid"]


class RadPostAuth(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=64, db_column="pass")
    reply = models.CharField(max_length=32)
    authdate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "radpostauth"
        ordering = ["-authdate"]


class RadAcctSyncState(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    last_radacctid = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "radacct_sync_state"
