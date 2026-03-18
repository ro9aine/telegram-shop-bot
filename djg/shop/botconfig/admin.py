from django.contrib import admin

from .models import RequiredChannel, TelegramProfile


@admin.register(RequiredChannel)
class RequiredChannelAdmin(admin.ModelAdmin):
    list_display = ("title", "chat_id", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "chat_id", "invite_link")


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("telegram_user_id", "phone_number", "username", "first_name", "last_name", "updated_at")
    search_fields = ("telegram_user_id", "phone_number", "username", "first_name", "last_name")
