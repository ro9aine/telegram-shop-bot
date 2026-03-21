from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0008_order_orderitem"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productimage",
            name="image_url",
            field=models.TextField(),
        ),
    ]
