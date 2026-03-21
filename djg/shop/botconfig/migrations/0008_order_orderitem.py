from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0007_telegramprofile_photo_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipient_name", models.CharField(max_length=255)),
                ("phone_number", models.CharField(max_length=32)),
                ("delivery_address", models.TextField()),
                ("delivery_comment", models.TextField(blank=True)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("status", models.CharField(choices=[("new", "New"), ("processing", "Processing"), ("done", "Done")], default="new", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="botconfig.telegramprofile")),
            ],
            options={
                "verbose_name": "Order",
                "verbose_name_plural": "Orders",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="botconfig.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="botconfig.product")),
            ],
            options={
                "verbose_name": "Order item",
                "verbose_name_plural": "Order items",
                "ordering": ["id"],
            },
        ),
    ]
