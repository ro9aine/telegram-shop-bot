from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0011_order_payment_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="BotSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("admin_chat_id", models.BigIntegerField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Bot settings",
                "verbose_name_plural": "Bot settings",
            },
        ),
        migrations.CreateModel(
            name="Broadcast",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=255)),
                ("text", models.TextField()),
                ("image_url", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("ready", "Ready"), ("sent", "Sent")],
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("delivered_count", models.PositiveIntegerField(default=0)),
                ("failed_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Broadcast",
                "verbose_name_plural": "Broadcasts",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="FAQ",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.CharField(max_length=255)),
                ("answer", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                ("is_popular", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "FAQ item",
                "verbose_name_plural": "FAQ items",
                "ordering": ["question"],
            },
        ),
    ]
