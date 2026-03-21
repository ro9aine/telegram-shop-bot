from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings


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

        admin_ids = _parse_admin_ids(get_settings().admin_telegram_ids)
        return user_id in admin_ids
