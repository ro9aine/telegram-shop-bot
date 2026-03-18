from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("telegram_user_id", models.BigIntegerField(unique=True)),
                ("username", models.CharField(blank=True, max_length=255)),
                ("first_name", models.CharField(blank=True, max_length=255)),
                ("last_name", models.CharField(blank=True, max_length=255)),
                ("phone_number", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["telegram_user_id"],
                "verbose_name": "Telegram profile",
                "verbose_name_plural": "Telegram profiles",
            },
        ),
    ]
