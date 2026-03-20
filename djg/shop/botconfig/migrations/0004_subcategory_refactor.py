from django.db import migrations, models
import django.db.models.deletion


def forward_refactor(apps, schema_editor):
    Category = apps.get_model("botconfig", "Category")
    Subcategory = apps.get_model("botconfig", "Subcategory")
    Product = apps.get_model("botconfig", "Product")

    sub_map = {}

    for category in Category.objects.exclude(parent_id=None).iterator():
        parent_id = category.parent_id
        if parent_id is None:
            continue
        subcategory, _ = Subcategory.objects.get_or_create(
            category_id=parent_id,
            title=category.title,
            defaults={"is_active": getattr(category, "is_active", True)},
        )
        sub_map[category.id] = subcategory.id

    for product in Product.objects.all().iterator():
        old_category_id = product.category_id
        sub_id = sub_map.get(old_category_id)
        if sub_id:
            old_category = Category.objects.filter(id=old_category_id).only("parent_id").first()
            if old_category and old_category.parent_id:
                product.category_id = old_category.parent_id
                product.subcategory_id = sub_id
                product.save(update_fields=["category_id", "subcategory_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("botconfig", "0003_catalog_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subcategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subcategories",
                        to="botconfig.category",
                    ),
                ),
            ],
            options={
                "ordering": ["title"],
                "verbose_name": "Subcategory",
                "verbose_name_plural": "Subcategories",
                "unique_together": {("category", "title")},
            },
        ),
        migrations.AddField(
            model_name="product",
            name="subcategory",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="botconfig.subcategory",
            ),
        ),
        migrations.RunPython(forward_refactor, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="category",
            name="parent",
        ),
    ]
