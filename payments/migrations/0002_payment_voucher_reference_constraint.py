from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0001_initial"),
        ("vouchers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="voucher",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="payments",
                to="vouchers.voucher",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="provider_reference",
            field=models.CharField(blank=True, db_index=True, max_length=128),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.UniqueConstraint(
                condition=~Q(provider_reference=""),
                fields=("provider", "provider_reference"),
                name="uniq_payment_provider_reference",
            ),
        ),
    ]
