from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE customers_customer SET phone = NULL WHERE phone = '';",
            reverse_sql="UPDATE customers_customer SET phone = '' WHERE phone IS NULL;",
        ),
        migrations.AlterField(
            model_name="customer",
            name="phone",
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]
