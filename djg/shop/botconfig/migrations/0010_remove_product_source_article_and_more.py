from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0009_alter_productimage_image_url"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="source_article",
        ),
        migrations.RemoveField(
            model_name="product",
            name="source_url",
        ),
    ]
