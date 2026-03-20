import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from app.config import get_settings
from app.storage.channels import load_required_channels

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("chat_id"))
async def handle_chat_id(message: Message) -> None:
    await message.answer(f"chat_id: {message.chat.id}")


@router.message(Command("resolve_chat"))
async def handle_resolve_chat(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Usage: /resolve_chat mash")
        return

    username = parts[1].strip()
    chat_ref = username if username.startswith("@") else f"@{username}"

    try:
        chat = await message.bot.get_chat(chat_ref)
    except Exception as exc:
        await message.answer(f"Failed to resolve {chat_ref}: {exc}")
        return

    await message.answer(
        f"title: {chat.title or '-'}\nusername: {chat.username or '-'}\nchat_id: {chat.id}",
    )


@router.message(Command("check_subs"))
async def handle_check_subs(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    if user_id is None:
        await message.answer("Cannot identify user.")
        return

    settings = get_settings()
    internal_api_token = (
        settings.internal_api_token.get_secret_value()
        if settings.internal_api_token is not None
        else None
    )
    channels = await load_required_channels(
        base_url=settings.django_api_base_url,
        internal_api_token=internal_api_token,
        cache_ttl=0,
    )
    if channels is None:
        await message.answer("Failed to fetch required channels from Django.")
        return
    if not channels:
        await message.answer("No required channels configured.")
        return

    lines = []
    for channel in channels:
        try:
            member = await message.bot.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            lines.append(f'{channel["title"]}: {member.status}')
        except TelegramAPIError as exc:
            lines.append(f'{channel["title"]}: ERROR {exc}')

    await message.answer("\n".join(lines))


@router.message()
async def handle_message(message: Message) -> None:
    logger.info(
        "Received message chat_id=%s user_id=%s text=%r",
        message.chat.id,
        message.from_user.id if message.from_user else None,
        message.text,
    )
    await message.answer(
        "I did not understand that message.\n"
        "Use /catalog to browse products or /start to begin.",
    )
