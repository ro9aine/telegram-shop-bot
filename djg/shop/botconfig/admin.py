from django.contrib import admin

from .models import BasketItem, Category, Order, OrderItem, Product, ProductImage, RequiredChannel, Subcategory, TelegramProfile


@admin.register(RequiredChannel)
class RequiredChannelAdmin(admin.ModelAdmin):
    list_display = ("title", "chat_id", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "chat_id", "invite_link")


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("telegram_user_id", "phone_number", "username", "first_name", "last_name", "photo_url", "updated_at")
    search_fields = ("telegram_user_id", "phone_number", "username", "first_name", "last_name", "photo_url")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title",)


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("title",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "source_article", "category", "subcategory", "price", "is_active", "updated_at")
    list_filter = ("is_active", "category", "subcategory")
    search_fields = ("title", "description", "source_article", "source_url")
    inlines = [ProductImageInline]


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ("profile", "product", "quantity", "updated_at")
    list_filter = ("updated_at",)
    search_fields = (
        "profile__telegram_user_id",
        "profile__phone_number",
        "product__title",
        "product__source_article",
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "title", "price", "quantity", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "recipient_name", "phone_number", "total_amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = (
        "id",
        "profile__telegram_user_id",
        "profile__phone_number",
        "recipient_name",
        "phone_number",
        "delivery_address",
    )
    inlines = [OrderItemInline]
