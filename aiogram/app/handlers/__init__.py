from aiogram import Router

from app.handlers.admin_chat import router as admin_chat_router
from app.handlers.catalog import router as catalog_router
from app.handlers.cart import router as cart_router
from app.handlers.faq import router as faq_router
from app.handlers.messages import router as messages_router
from app.handlers.registration import router as registration_router


def get_root_router() -> Router:
    router = Router()
    router.include_router(registration_router)
    router.include_router(catalog_router)
    router.include_router(cart_router)
    router.include_router(admin_chat_router)
    router.include_router(faq_router)
    router.include_router(messages_router)
    return router
