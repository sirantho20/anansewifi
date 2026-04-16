from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plans", "0002_remove_slug_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="is_featured",
            field=models.BooleanField(
                default=False,
                help_text="Highlight this plan on the public plans page (e.g. POPULAR ribbon).",
            ),
        ),
    ]
