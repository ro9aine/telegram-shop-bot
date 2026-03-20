from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0004_subcategory_refactor"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="source_article",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="product",
            name="source_url",
            field=models.URLField(blank=True),
        ),
    ]
