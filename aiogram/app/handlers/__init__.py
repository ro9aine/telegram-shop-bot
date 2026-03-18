from aiogram import Router

from app.handlers.messages import router as messages_router
from app.handlers.registration import router as registration_router


def get_root_router() -> Router:
    router = Router()
    router.include_router(registration_router)
    router.include_router(messages_router)
    return router
