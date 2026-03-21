from django.db import models


class RequiredChannel(models.Model):
    title = models.CharField(max_length=255)
    chat_id = models.CharField(max_length=64, unique=True)
    invite_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Required channel"
        verbose_name_plural = "Required channels"

    def __str__(self) -> str:
        return self.title


class TelegramProfile(models.Model):
    telegram_user_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    photo_url = models.URLField(blank=True)
    phone_number = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["telegram_user_id"]
        verbose_name = "Telegram profile"
        verbose_name_plural = "Telegram profiles"

    def __str__(self) -> str:
        return f"{self.telegram_user_id}: {self.phone_number}"


class Category(models.Model):
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.title


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        unique_together = ("category", "title")
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"

    def __str__(self) -> str:
        return f"{self.category.title} / {self.title}"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    subcategory = models.ForeignKey(
        Subcategory,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
    )
    source_article = models.CharField(max_length=64, unique=True, null=True, blank=True)
    source_url = models.URLField(blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField()
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Product image"
        verbose_name_plural = "Product images"

    def __str__(self) -> str:
        return f"{self.product_id}: {self.image_url}"


class BasketItem(models.Model):
    profile = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="basket_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="basket_items")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        unique_together = ("profile", "product")
        verbose_name = "Basket item"
        verbose_name_plural = "Basket items"

    def __str__(self) -> str:
        return f"{self.profile.telegram_user_id} -> {self.product_id} x{self.quantity}"


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_DONE, "Done"),
    ]

    profile = models.ForeignKey(TelegramProfile, on_delete=models.PROTECT, related_name="orders")
    recipient_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=32)
    delivery_address = models.TextField()
    delivery_comment = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self) -> str:
        return f"Order #{self.id} ({self.profile.telegram_user_id})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Order item"
        verbose_name_plural = "Order items"

    def __str__(self) -> str:
        return f"Order #{self.order_id}: {self.product_id} x{self.quantity}"
