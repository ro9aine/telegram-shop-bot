from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0006_basketitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegramprofile",
            name="photo_url",
            field=models.URLField(blank=True),
        ),
    ]

