from __future__ import annotations

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from app.config import get_settings
from app.storage.internal_api import search_faq

router = Router()


@router.inline_query()
async def handle_inline_faq(query: InlineQuery) -> None:
    settings = get_settings()
    internal_api_token = (
        settings.internal_api_token.get_secret_value()
        if settings.internal_api_token is not None
        else None
    )
    items = await search_faq(
        base_url=settings.django_api_base_url,
        internal_api_token=internal_api_token,
        query=query.query.strip(),
        limit=10,
    )

    results: list[InlineQueryResultArticle] = []
    for item in items:
        question = str(item.get("question") or "FAQ")
        answer = str(item.get("answer") or "-")
        faq_id = int(item.get("id") or 0)
        results.append(
            InlineQueryResultArticle(
                id=f"faq:{faq_id}",
                title=question,
                description=answer[:120],
                input_message_content=InputTextMessageContent(
                    message_text=f"{question}\n\n{answer}",
                ),
            )
        )

    await query.answer(results=results, cache_time=5, is_personal=True)
