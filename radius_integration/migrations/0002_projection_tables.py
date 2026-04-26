from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("radius_integration", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RadCheck",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(db_index=True, max_length=64)),
                ("attribute", models.CharField(max_length=64)),
                ("op", models.CharField(default=":=", max_length=2)),
                ("value", models.CharField(max_length=253)),
            ],
            options={
                "db_table": "radcheck",
                "ordering": ["username", "attribute"],
            },
        ),
        migrations.CreateModel(
            name="RadReply",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(db_index=True, max_length=64)),
                ("attribute", models.CharField(max_length=64)),
                ("op", models.CharField(default=":=", max_length=2)),
                ("value", models.CharField(max_length=253)),
            ],
            options={
                "db_table": "radreply",
                "ordering": ["username", "attribute"],
            },
        ),
        migrations.CreateModel(
            name="RadUserGroup",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(db_index=True, max_length=64)),
                ("groupname", models.CharField(max_length=64)),
                ("priority", models.PositiveIntegerField(default=1)),
            ],
            options={
                "db_table": "radusergroup",
                "ordering": ["username", "priority"],
            },
        ),
        migrations.CreateModel(
            name="RadGroupCheck",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("groupname", models.CharField(db_index=True, max_length=64)),
                ("attribute", models.CharField(max_length=64)),
                ("op", models.CharField(default=":=", max_length=2)),
                ("value", models.CharField(max_length=253)),
            ],
            options={
                "db_table": "radgroupcheck",
                "ordering": ["groupname", "attribute"],
            },
        ),
        migrations.CreateModel(
            name="RadGroupReply",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("groupname", models.CharField(db_index=True, max_length=64)),
                ("attribute", models.CharField(max_length=64)),
                ("op", models.CharField(default=":=", max_length=2)),
                ("value", models.CharField(max_length=253)),
            ],
            options={
                "db_table": "radgroupreply",
                "ordering": ["groupname", "attribute"],
            },
        ),
        migrations.CreateModel(
            name="RadAcct",
            fields=[
                ("radacctid", models.BigAutoField(primary_key=True, serialize=False)),
                ("acctsessionid", models.CharField(max_length=64)),
                ("acctuniqueid", models.CharField(max_length=32, unique=True)),
                ("username", models.CharField(db_index=True, max_length=64)),
                ("realm", models.CharField(blank=True, max_length=64, null=True)),
                ("nasipaddress", models.GenericIPAddressField(blank=True, null=True, protocol="IPv4")),
                ("nasportid", models.CharField(blank=True, max_length=15, null=True)),
                ("nasporttype", models.CharField(blank=True, max_length=32)),
                ("acctstarttime", models.DateTimeField(blank=True, null=True)),
                ("acctstartdelay", models.PositiveIntegerField(blank=True, null=True)),
                ("acctupdatetime", models.DateTimeField(blank=True, null=True)),
                ("acctstoptime", models.DateTimeField(blank=True, null=True)),
                ("acctstopdelay", models.PositiveIntegerField(blank=True, null=True)),
                ("acctinterval", models.PositiveIntegerField(blank=True, null=True)),
                ("acctsessiontime", models.PositiveIntegerField(blank=True, null=True)),
                ("acctauthentic", models.CharField(blank=True, max_length=32)),
                ("connectinfo_start", models.CharField(blank=True, max_length=50)),
                ("connectinfo_stop", models.CharField(blank=True, max_length=50, null=True)),
                ("acctinputoctets", models.BigIntegerField(default=0)),
                ("acctoutputoctets", models.BigIntegerField(default=0)),
                ("calledstationid", models.CharField(blank=True, max_length=50)),
                ("callingstationid", models.CharField(blank=True, max_length=50)),
                ("acctterminatecause", models.CharField(blank=True, max_length=32, null=True)),
                ("servicetype", models.CharField(blank=True, max_length=32)),
                ("framedprotocol", models.CharField(blank=True, max_length=32)),
                ("framedipaddress", models.GenericIPAddressField(blank=True, null=True, protocol="IPv4")),
                ("framedipv6address", models.GenericIPAddressField(blank=True, null=True)),
                ("framedipv6prefix", models.CharField(blank=True, max_length=45, null=True)),
                ("framedinterfaceid", models.CharField(blank=True, max_length=44, null=True)),
                ("delegatedipv6prefix", models.CharField(blank=True, max_length=45, null=True)),
                ("class_attribute", models.CharField(blank=True, db_column="class", max_length=64, null=True)),
                ("xascendsessionsvrkey", models.CharField(blank=True, max_length=10, null=True)),
            ],
            options={
                "db_table": "radacct",
                "ordering": ["-radacctid"],
            },
        ),
        migrations.CreateModel(
            name="RadPostAuth",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(max_length=64)),
                ("password", models.CharField(db_column="pass", max_length=64)),
                ("reply", models.CharField(max_length=32)),
                ("authdate", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "radpostauth",
                "ordering": ["-authdate"],
            },
        ),
        migrations.CreateModel(
            name="RadAcctSyncState",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("last_radacctid", models.BigIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "radacct_sync_state",
            },
        ),
        migrations.RunSQL(
            sql=(
                "INSERT INTO radcheck (username, attribute, op, value) "
                "SELECT username, attribute, op, value FROM radius_integration_radiuscheck"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "INSERT INTO radreply (username, attribute, op, value) "
                "SELECT username, attribute, op, value FROM radius_integration_radiusreply"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.DeleteModel(name="RadiusCheck"),
        migrations.DeleteModel(name="RadiusReply"),
    ]
