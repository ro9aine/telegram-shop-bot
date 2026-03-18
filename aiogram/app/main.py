import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import get_settings
from app.handlers import get_root_router
from app.middlewares.subscription import SubscriptionRequiredMiddleware

logger = logging.getLogger(__name__)


async def main() -> None:
    token = get_settings().bot_token.get_secret_value()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = Bot(token=token)
    dp = Dispatcher()
    subscription_middleware = SubscriptionRequiredMiddleware()
    dp.message.outer_middleware(subscription_middleware)
    dp.callback_query.outer_middleware(subscription_middleware)
    dp.include_router(get_root_router())
    logger.info("Starting bot polling")
    await dp.start_polling(bot)


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
