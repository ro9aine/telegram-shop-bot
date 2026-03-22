from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0012_faq_broadcast_botsettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="botsettings",
            name="admin_telegram_ids",
            field=models.TextField(blank=True, default=""),
        ),
    ]
