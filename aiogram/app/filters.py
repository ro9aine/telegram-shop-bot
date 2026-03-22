from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings
from app.storage.internal_api import load_bot_settings


def _parse_admin_ids(value: str) -> set[int]:
    result: set[int] = set()
    for part in value.split(","):
        raw = part.strip()
        if not raw:
            continue
        try:
            result.add(int(raw))
        except ValueError:
            continue
    return result


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user_id: int | None = None
        if isinstance(event, Message) and event.from_user is not None:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user is not None:
            user_id = event.from_user.id

        if user_id is None:
            return False

        settings = get_settings()
        internal_api_token = (
            settings.internal_api_token.get_secret_value()
            if settings.internal_api_token is not None
            else None
        )
        bot_settings = await load_bot_settings(
            base_url=settings.django_api_base_url,
            internal_api_token=internal_api_token,
            cache_ttl=settings.bot_settings_cache_ttl,
        )
        if bot_settings is None:
            return False

        admin_ids = _parse_admin_ids(str(bot_settings.get("admin_telegram_ids") or ""))
        admin_chat_id = bot_settings.get("admin_chat_id")
        if isinstance(admin_chat_id, int):
            admin_ids.add(admin_chat_id)
        else:
            try:
                if admin_chat_id is not None:
                    admin_ids.add(int(str(admin_chat_id)))
            except ValueError:
                pass

        return user_id in admin_ids
