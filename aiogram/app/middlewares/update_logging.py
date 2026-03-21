from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, InlineQuery, Message, TelegramObject

logger = logging.getLogger("bot.updates")


def _event_meta(event: TelegramObject) -> tuple[int | None, str]:
    if isinstance(event, Message):
        user_id = event.from_user.id if event.from_user else None
        return user_id, "message"
    if isinstance(event, CallbackQuery):
        user_id = event.from_user.id if event.from_user else None
        return user_id, "callback_query"
    if isinstance(event, InlineQuery):
        user_id = event.from_user.id if event.from_user else None
        return user_id, "inline_query"
    return None, type(event).__name__


class UpdateLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id, update_type = _event_meta(event)
        timestamp = datetime.now(timezone.utc).isoformat()
        logger.info("telegram_id=%s type=%s timestamp=%s", user_id, update_type, timestamp)
        return await handler(event, data)
