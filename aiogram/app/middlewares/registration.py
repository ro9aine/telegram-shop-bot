from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, InlineQuery, Message, TelegramObject

from app.config import get_settings
from app.storage.profiles import get_profile, sync_profile

logger = logging.getLogger(__name__)
_SYNC_CACHE_EXPIRES_AT: dict[int, float] = {}


def _event_user(event: TelegramObject):
    if isinstance(event, Message):
        return event.from_user
    if isinstance(event, CallbackQuery):
        return event.from_user
    if isinstance(event, InlineQuery):
        return event.from_user
    return None


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = _event_user(event)
        if user is None:
            return await handler(event, data)

        settings = get_settings()
        profile = get_profile(user.id) or {}
        data["client_profile"] = profile

        now = time.monotonic()
        ttl_seconds = 30.0
        if now >= _SYNC_CACHE_EXPIRES_AT.get(user.id, 0):
            internal_api_token = (
                settings.internal_api_token.get_secret_value()
                if settings.internal_api_token is not None
                else None
            )
            sync_ok = await asyncio.to_thread(
                sync_profile,
                base_url=settings.django_api_base_url,
                internal_api_token=internal_api_token,
                telegram_user_id=user.id,
                phone_number=str(profile.get("phone_number") or ""),
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                photo_url="",
            )
            if sync_ok:
                _SYNC_CACHE_EXPIRES_AT[user.id] = now + ttl_seconds
            else:
                logger.debug("Registration middleware sync skipped for user_id=%s", user.id)

        return await handler(event, data)
