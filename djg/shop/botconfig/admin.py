import base64
import csv
import mimetypes
from decimal import Decimal
from django.db.models import Count, Sum
from django.http import HttpResponse

from django import forms
from django.contrib import admin

from .models import (
    BasketItem,
    BotSettings,
    Broadcast,
    Category,
    FAQ,
    Order,
    OrderItem,
    Product,
    ProductImage,
    RequiredChannel,
    Subcategory,
    TelegramProfile,
)


class ProductImageInlineForm(forms.ModelForm):
    image_url = forms.CharField(required=False)
    image_file = forms.ImageField(required=False, help_text="Upload from desktop; it will be converted to Base64.")

    class Meta:
        model = ProductImage
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        image_file = cleaned_data.get("image_file")
        image_url = (cleaned_data.get("image_url") or "").strip()

        if image_file:
            mime_type = image_file.content_type or mimetypes.guess_type(image_file.name)[0] or "application/octet-stream"
            encoded = base64.b64encode(image_file.read()).decode("ascii")
            cleaned_data["image_url"] = f"data:{mime_type};base64,{encoded}"
            return cleaned_data

        if not image_url:
            self.add_error("image_url", "Provide an image URL or upload a file.")

        return cleaned_data


class ProfileOrderInline(admin.TabularInline):
    model = Order
    extra = 0
    fields = ("id", "created_at", "status", "payment_status", "total_amount")
    readonly_fields = fields
    can_delete = False
    show_change_link = True


@admin.register(RequiredChannel)
class RequiredChannelAdmin(admin.ModelAdmin):
    list_display = ("title", "chat_id", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "chat_id", "invite_link")


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_user_id",
        "phone_number",
        "username",
        "first_name",
        "last_name",
        "orders_count",
        "orders_total_amount",
        "updated_at",
    )
    search_fields = ("telegram_user_id", "phone_number", "username", "first_name", "last_name", "photo_url")
    readonly_fields = ("orders_count", "orders_total_amount")
    inlines = [ProfileOrderInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_orders_count=Count("orders", distinct=True), _orders_total_amount=Sum("orders__total_amount"))

    @admin.display(ordering="_orders_count", description="Orders")
    def orders_count(self, obj):
        return getattr(obj, "_orders_count", 0) or 0

    @admin.display(ordering="_orders_total_amount", description="Orders total")
    def orders_total_amount(self, obj):
        value = getattr(obj, "_orders_total_amount", None)
        if value is None:
            return Decimal("0.00")
        return value


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageInlineForm
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
    list_display = ("title", "category", "subcategory", "price", "is_active", "updated_at")
    list_filter = ("is_active", "category", "subcategory")
    search_fields = ("title", "description")
    inlines = [ProductImageInline]


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ("profile", "product", "quantity", "updated_at")
    list_filter = ("updated_at",)
    search_fields = (
        "profile__telegram_user_id",
        "profile__phone_number",
        "product__title",
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "title", "price", "quantity", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "recipient_name", "phone_number", "total_amount", "status", "payment_status", "created_at")
    list_filter = ("status", "payment_status", "created_at")
    search_fields = (
        "id",
        "profile__telegram_user_id",
        "profile__phone_number",
        "recipient_name",
        "phone_number",
        "delivery_address",
    )
    inlines = [OrderItemInline]
    actions = ("export_paid_orders_csv",)

    @admin.action(description="Export selected paid orders to CSV (Excel-compatible)")
    def export_paid_orders_csv(self, request, queryset):
        paid = queryset.filter(payment_status=Order.PAYMENT_PAID).select_related("profile")

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="paid-orders.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Order ID",
                "Telegram User ID",
                "Recipient",
                "Phone",
                "Address",
                "Total",
                "Status",
                "Payment Status",
                "Created At",
            ]
        )
        for order in paid:
            writer.writerow(
                [
                    order.id,
                    order.profile.telegram_user_id,
                    order.recipient_name,
                    order.phone_number,
                    order.delivery_address,
                    order.total_amount,
                    order.status,
                    order.payment_status,
                    order.created_at.isoformat(),
                ]
            )
        return response


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "is_popular", "updated_at")
    list_filter = ("is_active", "is_popular")
    search_fields = ("question", "answer")


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "delivered_count", "failed_count", "created_at", "sent_at")
    list_filter = ("status", "created_at", "sent_at")
    search_fields = ("title", "text")


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ("admin_chat_id", "updated_at")

    def has_add_permission(self, request):
        if BotSettings.objects.exists():
            return False
        return super().has_add_permission(request)
