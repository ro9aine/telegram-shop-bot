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
    phone_number = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["telegram_user_id"]
        verbose_name = "Telegram profile"
        verbose_name_plural = "Telegram profiles"

    def __str__(self) -> str:
        return f"{self.telegram_user_id}: {self.phone_number}"
