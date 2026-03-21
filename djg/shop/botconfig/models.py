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
    image_url = models.TextField()
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
    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PAID = "paid"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PAID, "Paid"),
    ]

    profile = models.ForeignKey(TelegramProfile, on_delete=models.PROTECT, related_name="orders")
    recipient_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=32)
    delivery_address = models.TextField()
    delivery_comment = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW)
    payment_status = models.CharField(
        max_length=16,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_UNPAID,
    )
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


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["question"]
        verbose_name = "FAQ item"
        verbose_name_plural = "FAQ items"

    def __str__(self) -> str:
        return self.question


class Broadcast(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_READY = "ready"
    STATUS_SENT = "sent"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_READY, "Ready"),
        (STATUS_SENT, "Sent"),
    ]

    title = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    image_url = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    delivered_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Broadcast"
        verbose_name_plural = "Broadcasts"

    def __str__(self) -> str:
        label = self.title.strip() if self.title else f"Broadcast #{self.id}"
        return f"{label} [{self.status}]"


class BotSettings(models.Model):
    admin_chat_id = models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bot settings"
        verbose_name_plural = "Bot settings"

    def __str__(self) -> str:
        return f"Bot settings (admin_chat_id={self.admin_chat_id or '-'})"
