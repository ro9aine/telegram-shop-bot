import logging
from typing import Any, Awaitable, Callable

from aiogram import Bot
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, InlineQuery, Message, TelegramObject

from app.config import get_settings
from app.keyboards import subscription_prompt
from app.storage.channels import load_required_channels

logger = logging.getLogger(__name__)


class SubscriptionRequiredMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        bot: Bot = data["bot"]
        settings = get_settings()
        internal_api_token = (
            settings.internal_api_token.get_secret_value()
            if settings.internal_api_token is not None
            else None
        )
        channels = await load_required_channels(
            base_url=settings.django_api_base_url,
            internal_api_token=internal_api_token,
            cache_ttl=settings.required_channels_cache_ttl,
        )
        if channels is None:
            text = "Subscription check is temporarily unavailable. Try again in a moment."
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery) and event.message is not None:
                await event.message.answer(text)
                await event.answer()
            elif isinstance(event, InlineQuery):
                await event.answer(results=[], cache_time=2, is_personal=True)
            return None

        if not channels:
            return await handler(event, data)

        chat = getattr(event, "chat", None)
        if chat is not None:
            current_chat_id = str(chat.id)
            if any(channel["chat_id"] == current_chat_id for channel in channels):
                logger.info("Ignoring update from required channel chat_id=%s", current_chat_id)
                return None

        missing_channels: list[dict[str, str]] = []
        for channel in channels:
            try:
                member = await bot.get_chat_member(chat_id=channel["chat_id"], user_id=user.id)
            except TelegramAPIError as exc:
                logger.warning(
                    "Failed to check membership user_id=%s chat_id=%s error=%s",
                    user.id,
                    channel["chat_id"],
                    exc,
                )
                missing_channels.append(channel)
                continue
            if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}:
                missing_channels.append(channel)

        if not missing_channels:
            return await handler(event, data)

        logger.info("Blocked unsubscribed user_id=%s missing=%s", user.id, missing_channels)
        text = "Access is available only after subscription.\nSubscribe to the required channels and send /start again."
        reply_markup = subscription_prompt(missing_channels)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=reply_markup)
        elif isinstance(event, CallbackQuery) and event.message is not None:
            await event.message.answer(text, reply_markup=reply_markup)
            await event.answer()
        elif isinstance(event, InlineQuery):
            await event.answer(
                results=[],
                cache_time=2,
                is_personal=True,
                switch_pm_text="Subscription required",
                switch_pm_parameter="start",
            )

        return None
