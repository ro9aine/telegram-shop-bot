import logging
import asyncio

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from app.config import get_settings
from app.keyboards import contact_request_keyboard
from app.storage.profiles import get_profile, save_profile, sync_profile

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    logger.info("Handled /start for chat_id=%s", message.chat.id)
    user_id = message.from_user.id if message.from_user else None
    if user_id is None:
        await message.answer("Cannot identify user.")
        return

    if get_profile(user_id):
        await message.answer("You are already registered.", reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(
        "Please share your phone number to complete registration.",
        reply_markup=contact_request_keyboard(),
    )


@router.message(F.contact)
async def handle_contact(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    contact = message.contact
    if user_id is None or contact is None:
        await message.answer("Cannot save contact.")
        return

    if contact.user_id is not None and contact.user_id != user_id:
        logger.warning("Rejected foreign contact chat_id=%s user_id=%s", message.chat.id, user_id)
        await message.answer(
            "Send your own contact using the button below.",
            reply_markup=contact_request_keyboard(),
        )
        return

    save_profile(user_id, contact.phone_number)
    settings = get_settings()
    internal_api_token = (
        settings.internal_api_token.get_secret_value()
        if settings.internal_api_token is not None
        else None
    )
    sync_ok = await asyncio.to_thread(
        sync_profile,
        base_url=settings.django_api_base_url,
        internal_api_token=internal_api_token,
        telegram_user_id=user_id,
        phone_number=contact.phone_number,
        username=message.from_user.username if message.from_user else "",
        first_name=message.from_user.first_name if message.from_user else "",
        last_name=message.from_user.last_name if message.from_user else "",
    )
    logger.info("Saved phone for user_id=%s", user_id)
    if not sync_ok:
        logger.warning("Profile sync did not complete for user_id=%s", user_id)
    await message.answer("Registration completed.", reply_markup=ReplyKeyboardRemove())
