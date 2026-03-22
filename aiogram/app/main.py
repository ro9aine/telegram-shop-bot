import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from app.config import get_settings
from app.handlers import get_root_router
from app.middlewares.registration import RegistrationMiddleware
from app.middlewares.subscription import SubscriptionRequiredMiddleware
from app.middlewares.update_logging import UpdateLoggingMiddleware
from app.storage.internal_api import load_next_broadcast, mark_broadcast_complete

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand(command="start", description="Start bot"),
    BotCommand(command="catalog", description="Open catalog"),
    BotCommand(command="cart", description="Open cart"),
    BotCommand(command="chat_id", description="Show current chat id"),
    BotCommand(command="help", description="Help"),
]


def _configure_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=log_dir / "bot.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), file_handler],
    )


async def _broadcast_worker(bot: Bot) -> None:
    settings = get_settings()
    internal_api_token = (
        settings.internal_api_token.get_secret_value() if settings.internal_api_token is not None else None
    )
    sleep_seconds = max(3, settings.broadcast_poll_interval_seconds)

    while True:
        try:
            broadcast = await load_next_broadcast(
                base_url=settings.django_api_base_url,
                internal_api_token=internal_api_token,
            )
            if not broadcast:
                await asyncio.sleep(sleep_seconds)
                continue

            broadcast_id = int(broadcast.get("id") or 0)
            recipients = [int(item) for item in broadcast.get("recipients", [])]
            text = str(broadcast.get("text") or "")
            image_url = str(broadcast.get("image_url") or "").strip()

            delivered_count = 0
            failed_count = 0
            for chat_id in recipients:
                try:
                    if image_url and image_url.startswith("http"):
                        await bot.send_photo(chat_id=chat_id, photo=image_url, caption=text or None)
                    else:
                        await bot.send_message(chat_id=chat_id, text=text or "Broadcast")
                    delivered_count += 1
                except Exception:
                    failed_count += 1

            if broadcast_id:
                await mark_broadcast_complete(
                    base_url=settings.django_api_base_url,
                    internal_api_token=internal_api_token,
                    broadcast_id=broadcast_id,
                    delivered_count=delivered_count,
                    failed_count=failed_count,
                )
        except Exception:
            logger.exception("Broadcast worker error")
            await asyncio.sleep(sleep_seconds)


async def main() -> None:
    token = get_settings().bot_token.get_secret_value()
    _configure_logging()

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    update_logging_middleware = UpdateLoggingMiddleware()
    registration_middleware = RegistrationMiddleware()
    subscription_middleware = SubscriptionRequiredMiddleware()

    dp.message.outer_middleware(update_logging_middleware)
    dp.callback_query.outer_middleware(update_logging_middleware)
    dp.inline_query.outer_middleware(update_logging_middleware)

    dp.message.outer_middleware(registration_middleware)
    dp.callback_query.outer_middleware(registration_middleware)
    dp.inline_query.outer_middleware(registration_middleware)

    dp.message.outer_middleware(subscription_middleware)
    dp.callback_query.outer_middleware(subscription_middleware)
    dp.inline_query.outer_middleware(subscription_middleware)
    dp.include_router(get_root_router())

    await bot.set_my_commands(BOT_COMMANDS)
    asyncio.create_task(_broadcast_worker(bot))

    logger.info("Starting bot polling")
    await dp.start_polling(bot)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
