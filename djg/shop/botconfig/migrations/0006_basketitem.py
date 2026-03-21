from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0005_product_source_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="BasketItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="basket_items",
                        to="botconfig.product",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="basket_items",
                        to="botconfig.telegramprofile",
                    ),
                ),
            ],
            options={
                "verbose_name": "Basket item",
                "verbose_name_plural": "Basket items",
                "ordering": ["-updated_at", "-id"],
                "unique_together": {("profile", "product")},
            },
        ),
    ]

