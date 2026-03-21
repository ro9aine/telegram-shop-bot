from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0010_remove_product_source_article_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[("unpaid", "Unpaid"), ("paid", "Paid")],
                default="unpaid",
                max_length=16,
            ),
        ),
    ]
