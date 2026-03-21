import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import BotSettings, Order

logger = logging.getLogger(__name__)


def _send_telegram_message(*, bot_token: str, chat_id: int, text: str) -> bool:
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
        }
    ).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5):
            return True
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.warning("Failed to notify user about order status change chat_id=%s error=%s", chat_id, exc)
        return False


def _send_telegram_message_with_keyboard(*, bot_token: str, chat_id: int, text: str, keyboard: dict) -> bool:
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": keyboard,
        }
    ).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5):
            return True
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.warning("Failed to send admin order notification chat_id=%s error=%s", chat_id, exc)
        return False


@receiver(pre_save, sender=Order)
def _remember_previous_order_status(sender, instance: Order, **kwargs) -> None:
    if not instance.pk:
        instance._previous_status = None
        return
    previous = Order.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    instance._previous_status = previous


@receiver(post_save, sender=Order)
def _notify_order_status_changed(sender, instance: Order, created: bool, **kwargs) -> None:
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)
    if not previous_status or previous_status == instance.status:
        return

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not configured. Skip order status notification for order_id=%s", instance.id)
        return

    user_chat_id = instance.profile.telegram_user_id
    text = (
        f"Order #{instance.id} status updated.\n"
        f"New status: {instance.get_status_display()}."
    )
    _send_telegram_message(bot_token=bot_token, chat_id=user_chat_id, text=text)


@receiver(post_save, sender=Order)
def _notify_admin_chat_about_new_order(sender, instance: Order, created: bool, **kwargs) -> None:
    if not created:
        return

    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return

    bot_settings = BotSettings.objects.first()
    if bot_settings is None or not bot_settings.admin_chat_id:
        return

    text = (
        f"New order #{instance.id}\n"
        f"User: {instance.profile.telegram_user_id}\n"
        f"Recipient: {instance.recipient_name}\n"
        f"Phone: {instance.phone_number}\n"
        f"Address: {instance.delivery_address}\n"
        f"Total: {instance.total_amount}"
    )
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Processing", "callback_data": f"admord:{instance.id}:processing"},
                {"text": "Done", "callback_data": f"admord:{instance.id}:done"},
            ]
        ]
    }
    _send_telegram_message_with_keyboard(
        bot_token=bot_token,
        chat_id=bot_settings.admin_chat_id,
        text=text,
        keyboard=keyboard,
    )
