from __future__ import annotations

import asyncio
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InputMediaPhoto, Message

from app.callbacks import (
    CatalogBackCallback,
    CatalogCategoryCallback,
    CatalogPageCallback,
    CatalogProductCallback,
    CartAddCallback,
)
from app.config import get_settings
from app.keyboards import catalog_categories_keyboard, catalog_products_keyboard, product_card_keyboard
from app.storage.cart import add_to_cart
from app.storage.catalog import load_categories, load_product, load_products

router = Router()

MAX_TEXT_MESSAGE_LEN = 700
MAX_DESCRIPTION_PREVIEW_LEN = 180
IMAGE_FETCH_TIMEOUT_SECONDS = 6
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_ALBUM_IMAGES = 10
_PRODUCT_TEMP_MESSAGES: dict[tuple[int, int], list[int]] = {}


def _trim_text(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _preview_description(value: str, limit: int = MAX_DESCRIPTION_PREVIEW_LEN) -> str:
    normalized = " ".join(value.split())
    return _trim_text(normalized, limit)


def _download_image(url: str) -> bytes | None:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=IMAGE_FETCH_TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_IMAGE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError):
        return None

    if not payload or len(payload) > MAX_IMAGE_BYTES:
        return None
    return payload


async def _download_album_images(urls: list[str]) -> list[bytes]:
    tasks = [asyncio.to_thread(_download_image, url) for url in urls[:MAX_ALBUM_IMAGES]]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return [item for item in results if item]


async def _send_product_card_message(
    message: Message,
    *,
    product_id: int,
    category_id: int | None,
    page: int | None,
) -> bool:
    settings = get_settings()
    product = await load_product(settings.django_api_base_url, product_id)
    if product is None:
        await message.answer("Product not found.")
        return False

    title = str(product.get("title", "Product")).strip()
    description = _preview_description(str(product.get("description", "")))
    price_line = f'Price: {product.get("price", "-")}'
    text_message = _trim_text("\n".join(line for line in [title, description, price_line] if line), MAX_TEXT_MESSAGE_LEN)

    resolved_category_id = category_id
    raw_category_id = product.get("category_id")
    if resolved_category_id is None and isinstance(raw_category_id, int):
        resolved_category_id = raw_category_id

    keyboard = product_card_keyboard(
        product_id=product_id,
        category_id=resolved_category_id,
        page=page if resolved_category_id is not None else None,
        webapp_url=settings.webapp_catalog_url,
    )

    image_urls = [str(image) for image in product.get("images", []) if image]
    album_bytes = await _download_album_images(image_urls) if image_urls else []

    if album_bytes:
        media: list[InputMediaPhoto] = []
        for idx, payload in enumerate(album_bytes):
            file = BufferedInputFile(payload, filename=f"product-{product_id}-{idx + 1}.jpg")
            if idx == 0:
                media.append(InputMediaPhoto(media=file, caption=text_message))
            else:
                media.append(InputMediaPhoto(media=file))
        try:
            await message.answer_media_group(media=media)
            await message.answer("Choose an action:", reply_markup=keyboard)
            return True
        except Exception:
            pass

    await message.answer(text_message, reply_markup=keyboard, disable_web_page_preview=True)
    return True


def _children(categories: list[dict], parent_id: int | None) -> list[dict]:
    return sorted(
        [item for item in categories if item.get("parent_id") == parent_id],
        key=lambda item: str(item.get("title", "")),
    )


def _category_by_id(categories: list[dict], category_id: int) -> dict | None:
    for category in categories:
        if category.get("id") == category_id:
            return category
    return None


def _session_key(chat_id: int, user_id: int) -> tuple[int, int]:
    return (chat_id, user_id)


async def _cleanup_product_album_messages(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        return

    current_message_id = callback.message.message_id
    key = _session_key(callback.message.chat.id, callback.from_user.id)
    message_ids = _PRODUCT_TEMP_MESSAGES.pop(key, [])
    if not message_ids:
        return

    remaining: list[int] = []
    for message_id in message_ids:
        if message_id == current_message_id:
            remaining.append(message_id)
            continue
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=message_id)
        except Exception:
            remaining.append(message_id)

    if remaining:
        _PRODUCT_TEMP_MESSAGES[key] = remaining


async def _show_categories(target: Message | CallbackQuery, parent_id: int | None) -> None:
    settings = get_settings()
    categories = await load_categories(settings.django_api_base_url)
    if not categories:
        text = "Catalog is empty."
        if isinstance(target, Message):
            await target.answer(text)
        else:
            await target.message.edit_text(text)
        return

    current = _children(categories, parent_id)
    if not current:
        text = "No categories found."
        if isinstance(target, Message):
            await target.answer(text)
        else:
            await target.message.edit_text(text)
        return

    parent_for_back: int | None = None
    if parent_id is not None:
        parent_category = _category_by_id(categories, parent_id)
        parent_for_back = parent_category.get("parent_id") if parent_category else None
        if parent_for_back is None:
            parent_for_back = 0

    keyboard = catalog_categories_keyboard(
        categories=current,
        webapp_url=settings.webapp_catalog_url,
        parent_id=parent_for_back,
    )
    title = "Choose category:" if parent_id is None else "Choose subcategory:"

    if isinstance(target, Message):
        await target.answer(title, reply_markup=keyboard)
    else:
        await target.message.edit_text(title, reply_markup=keyboard)


async def _show_products(callback: CallbackQuery, category_id: int, page: int) -> None:
    settings = get_settings()
    categories = await load_categories(settings.django_api_base_url)
    category = _category_by_id(categories, category_id)
    payload = await load_products(settings.django_api_base_url, category_id=category_id, page=page, page_size=5)
    products = payload.get("items", [])
    pagination = payload.get("pagination", {})
    current_page = int(pagination.get("page", page))
    total_pages = int(pagination.get("total_pages", 1))

    keyboard = catalog_products_keyboard(
        products=products,
        category_id=category_id,
        page=current_page,
        total_pages=total_pages,
        parent_id=category.get("parent_id") if category else None,
        webapp_url=settings.webapp_catalog_url,
    )

    if not products:
        await callback.message.edit_text("No products in this category yet.", reply_markup=keyboard)
        return

    category_title = category.get("title") if category else "Category"
    await callback.message.edit_text(
        f"{category_title}\nPage {current_page}/{total_pages}",
        reply_markup=keyboard,
    )


@router.message(Command("catalog"))
async def handle_catalog(message: Message) -> None:
    await _show_categories(message, parent_id=None)


@router.callback_query(CatalogBackCallback.filter())
async def handle_catalog_back(callback: CallbackQuery, callback_data: CatalogBackCallback) -> None:
    await _cleanup_product_album_messages(callback)
    await _show_categories(callback, parent_id=callback_data.parent_id or None)
    await callback.answer()


@router.callback_query(CatalogCategoryCallback.filter())
async def handle_catalog_category(callback: CallbackQuery, callback_data: CatalogCategoryCallback) -> None:
    await _cleanup_product_album_messages(callback)
    settings = get_settings()
    categories = await load_categories(settings.django_api_base_url)
    subcategories = _children(categories, callback_data.category_id)
    if subcategories:
        current = _category_by_id(categories, callback_data.category_id)
        parent_for_back = current.get("parent_id") if current else None
        if parent_for_back is None:
            parent_for_back = 0
        await callback.message.edit_text(
            "Choose subcategory:",
            reply_markup=catalog_categories_keyboard(
                categories=subcategories,
                webapp_url=settings.webapp_catalog_url,
                parent_id=parent_for_back,
            ),
        )
        await callback.answer()
        return

    await _show_products(callback, category_id=callback_data.category_id, page=1)
    await callback.answer()


@router.callback_query(CatalogPageCallback.filter())
async def handle_catalog_page(callback: CallbackQuery, callback_data: CatalogPageCallback) -> None:
    await _cleanup_product_album_messages(callback)
    await _show_products(callback, category_id=callback_data.category_id, page=callback_data.page)
    await callback.answer()


@router.callback_query(CatalogProductCallback.filter())
async def handle_catalog_product(callback: CallbackQuery, callback_data: CatalogProductCallback) -> None:
    await _cleanup_product_album_messages(callback)
    settings = get_settings()
    product = await load_product(settings.django_api_base_url, callback_data.product_id)
    if product is None:
        await callback.answer("Product not found", show_alert=True)
        return

    title = str(product.get("title", "Product")).strip()
    description = _preview_description(str(product.get("description", "")))
    price_line = f'Price: {product.get("price", "-")}'
    text_message = _trim_text("\n".join(line for line in [title, description, price_line] if line), MAX_TEXT_MESSAGE_LEN)
    keyboard = product_card_keyboard(
        product_id=callback_data.product_id,
        category_id=callback_data.category_id,
        page=callback_data.page,
        webapp_url=settings.webapp_catalog_url,
    )

    image_urls = [str(image) for image in product.get("images", []) if image]
    album_bytes = await _download_album_images(image_urls) if image_urls else []

    album_sent = False
    if album_bytes:
        media: list[InputMediaPhoto] = []
        for idx, payload in enumerate(album_bytes):
            file = BufferedInputFile(payload, filename=f"product-{callback_data.product_id}-{idx + 1}.jpg")
            if idx == 0:
                media.append(InputMediaPhoto(media=file, caption=text_message))
            else:
                media.append(InputMediaPhoto(media=file))
        try:
            sent_messages = await callback.message.answer_media_group(media=media)
            album_sent = True
            if callback.from_user is not None:
                key = _session_key(callback.message.chat.id, callback.from_user.id)
                _PRODUCT_TEMP_MESSAGES[key] = [message.message_id for message in sent_messages]
        except Exception:
            pass

    if album_sent:
        actions_message = await callback.message.answer(
            "Choose an action:",
            reply_markup=keyboard,
        )
        if callback.from_user is not None:
            key = _session_key(callback.message.chat.id, callback.from_user.id)
            _PRODUCT_TEMP_MESSAGES.setdefault(key, []).append(actions_message.message_id)
        try:
            await callback.message.delete()
        except Exception:
            pass
    else:
        await callback.message.edit_text(
            text_message,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    await callback.answer()


async def show_product_from_start(message: Message, product_id: int) -> bool:
    return await _send_product_card_message(
        message,
        product_id=product_id,
        category_id=None,
        page=1,
    )


@router.callback_query(CartAddCallback.filter())
async def handle_cart_add(callback: CallbackQuery, callback_data: CartAddCallback) -> None:
    user_id = callback.from_user.id
    quantity = add_to_cart(user_id=user_id, product_id=callback_data.product_id, quantity=1)
    await callback.answer(f"Added. Quantity: {quantity}")
