from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.callbacks import AdminOrderStatusCallback
from app.config import get_settings
from app.filters import IsAdmin
from app.storage.internal_api import load_active_orders, load_bot_settings, set_order_status

router = Router()


def _order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Processing",
                    callback_data=AdminOrderStatusCallback(order_id=order_id, status="processing").pack(),
                ),
                InlineKeyboardButton(
                    text="Done",
                    callback_data=AdminOrderStatusCallback(order_id=order_id, status="done").pack(),
                ),
            ]
        ]
    )


def _order_text(order: dict) -> str:
    items = order.get("items", [])
    lines = [
        f'Order #{order.get("id")}',
        f'Status: {order.get("status")}',
        f'Payment: {order.get("payment_status")}',
        f'User: {order.get("telegram_user_id")}',
        f'Recipient: {order.get("recipient_name")}',
        f'Phone: {order.get("phone_number")}',
        f'Address: {order.get("delivery_address")}',
        f'Total: {order.get("total_amount")}',
        "",
        "Items:",
    ]
    for item in items:
        lines.append(f"- {item.get('title')} x{item.get('quantity')} ({item.get('price')})")
    return "\n".join(lines)


@router.message(IsAdmin(), Command("admin_orders"))
async def handle_admin_orders(message: Message) -> None:
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
    admin_chat_id = bot_settings.get("admin_chat_id") if bot_settings else None
    if admin_chat_id is not None and message.chat.id != int(admin_chat_id):
        await message.answer("This command is available only in admin chat.")
        return

    orders = await load_active_orders(settings.django_api_base_url, internal_api_token)
    if not orders:
        await message.answer("No active orders.")
        return

    for order in orders[:20]:
        await message.answer(
            _order_text(order),
            reply_markup=_order_actions_keyboard(int(order.get("id") or 0)),
        )


@router.callback_query(IsAdmin(), AdminOrderStatusCallback.filter())
async def handle_admin_order_status(
    callback: CallbackQuery,
    callback_data: AdminOrderStatusCallback,
) -> None:
    await _apply_admin_order_status(callback, callback_data)


async def _apply_admin_order_status(callback: CallbackQuery, callback_data: AdminOrderStatusCallback) -> None:
    if not await IsAdmin()(callback):
        await callback.answer("Admins only", show_alert=True)
        return

    settings = get_settings()
    internal_api_token = (
        settings.internal_api_token.get_secret_value()
        if settings.internal_api_token is not None
        else None
    )
    ok = await set_order_status(
        base_url=settings.django_api_base_url,
        internal_api_token=internal_api_token,
        order_id=callback_data.order_id,
        status=callback_data.status,
    )
    if not ok:
        await callback.answer("Failed to update status", show_alert=True)
        return

    await callback.answer("Order status updated")
    if callback.message is not None:
        text = (callback.message.text or "").split("\n")
        if len(text) > 1 and text[1].startswith("Status:"):
            text[1] = f"Status: {callback_data.status}"
            await callback.message.edit_text("\n".join(text), reply_markup=callback.message.reply_markup)
