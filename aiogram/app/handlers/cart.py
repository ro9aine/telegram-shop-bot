from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.callbacks import (
    CartAddCallback,
    CartChangeQtyCallback,
    CartCheckoutCallback,
    CartClearCallback,
    CartRemoveCallback,
    CheckoutFlowCallback,
    OrderPaidCallback,
)
from app.config import get_settings
from app.keyboards import cart_actions_keyboard, cart_item_keyboard, checkout_confirm_keyboard, order_paid_keyboard
from app.storage.internal_api import (
    add_internal_basket_item,
    checkout_internal_order,
    clear_internal_basket,
    load_internal_basket,
    mark_internal_order_paid,
    remove_internal_basket_item,
    update_internal_basket_item,
)
from app.storage.profiles import get_profile

router = Router()


class CheckoutStates(StatesGroup):
    recipient_name = State()
    delivery_address = State()
    confirm = State()


def _internal_token() -> str | None:
    settings = get_settings()
    return settings.internal_api_token.get_secret_value() if settings.internal_api_token is not None else None


def _basket_total(items: list[dict]) -> Decimal:
    total = Decimal("0")
    for item in items:
        try:
            total += Decimal(str(item.get("price") or "0")) * int(item.get("quantity") or 0)
        except Exception:
            continue
    return total


async def _render_cart(message: Message, telegram_user_id: int) -> None:
    settings = get_settings()
    items = await load_internal_basket(settings.django_api_base_url, _internal_token(), telegram_user_id)
    if not items:
        await message.answer("Your cart is empty.")
        return

    for item in items:
        await message.answer(
            f'{item.get("title")} x{item.get("quantity")} • {item.get("price")}',
            reply_markup=cart_item_keyboard(int(item.get("product_id") or 0)),
        )

    await message.answer(
        f"Total: {_basket_total(items)}",
        reply_markup=cart_actions_keyboard(),
    )


@router.message(Command("cart"))
async def handle_cart(message: Message) -> None:
    if message.from_user is None:
        await message.answer("Cannot identify user.")
        return
    await _render_cart(message, message.from_user.id)


@router.callback_query(CartChangeQtyCallback.filter())
async def handle_cart_change_qty(callback: CallbackQuery, callback_data: CartChangeQtyCallback) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Cannot identify user", show_alert=True)
        return

    settings = get_settings()
    items = await load_internal_basket(settings.django_api_base_url, _internal_token(), callback.from_user.id)
    target = next((item for item in items if int(item.get("product_id") or 0) == callback_data.product_id), None)
    if target is None:
        await callback.answer("Item not found", show_alert=True)
        return

    new_quantity = int(target.get("quantity") or 0) + callback_data.delta
    if new_quantity <= 0:
        items = await remove_internal_basket_item(
            settings.django_api_base_url,
            _internal_token(),
            telegram_user_id=callback.from_user.id,
            product_id=callback_data.product_id,
        )
        await callback.answer("Item removed")
    else:
        items = await update_internal_basket_item(
            settings.django_api_base_url,
            _internal_token(),
            telegram_user_id=callback.from_user.id,
            product_id=callback_data.product_id,
            quantity=new_quantity,
        )
        await callback.answer(f"Quantity: {new_quantity}")

    updated = next((item for item in items if int(item.get("product_id") or 0) == callback_data.product_id), None)
    if updated is None:
        await callback.message.edit_text("Removed from cart.")
        return
    await callback.message.edit_text(
        f'{updated.get("title")} x{updated.get("quantity")} • {updated.get("price")}',
        reply_markup=cart_item_keyboard(callback_data.product_id),
    )


@router.callback_query(CartRemoveCallback.filter())
async def handle_cart_remove(callback: CallbackQuery, callback_data: CartRemoveCallback) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Cannot identify user", show_alert=True)
        return

    settings = get_settings()
    await remove_internal_basket_item(
        settings.django_api_base_url,
        _internal_token(),
        telegram_user_id=callback.from_user.id,
        product_id=callback_data.product_id,
    )
    await callback.message.edit_text("Removed from cart.")
    await callback.answer("Removed")


@router.callback_query(CartClearCallback.filter())
async def handle_cart_clear(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Cannot identify user", show_alert=True)
        return

    settings = get_settings()
    await clear_internal_basket(settings.django_api_base_url, _internal_token(), callback.from_user.id)
    await callback.answer("Cart cleared")
    if callback.message is not None:
        await callback.message.answer("Cart cleared.")


@router.callback_query(CartCheckoutCallback.filter())
async def handle_cart_checkout_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Cannot identify user", show_alert=True)
        return
    await state.clear()
    await state.set_state(CheckoutStates.recipient_name)
    profile = get_profile(callback.from_user.id) or {}
    phone = profile.get("phone_number") or "-"
    await callback.message.answer(f"Enter recipient name.\nPhone from profile: {phone}")
    await callback.answer()


@router.message(CheckoutStates.recipient_name)
async def handle_checkout_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Recipient name is required.")
        return
    await state.update_data(recipient_name=name)
    await state.set_state(CheckoutStates.delivery_address)
    await message.answer("Enter delivery address:")


@router.message(CheckoutStates.delivery_address)
async def handle_checkout_address(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()
    if not address:
        await message.answer("Address is required.")
        return
    await state.update_data(delivery_address=address)
    data = await state.get_data()
    await state.set_state(CheckoutStates.confirm)
    await message.answer(
        f"Confirm order?\nRecipient: {data.get('recipient_name')}\nAddress: {address}",
        reply_markup=checkout_confirm_keyboard(),
    )


@router.callback_query(CheckoutFlowCallback.filter(F.action == "cancel"))
async def handle_checkout_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Checkout canceled")
    if callback.message is not None:
        await callback.message.edit_text("Checkout canceled.")


@router.callback_query(CheckoutFlowCallback.filter(F.action == "confirm"))
async def handle_checkout_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Cannot identify user", show_alert=True)
        return
    data = await state.get_data()
    recipient_name = str(data.get("recipient_name") or "").strip()
    delivery_address = str(data.get("delivery_address") or "").strip()
    profile = get_profile(callback.from_user.id) or {}
    phone = str(profile.get("phone_number") or "").strip()
    if not recipient_name or not delivery_address:
        await callback.answer("Checkout data is incomplete", show_alert=True)
        return

    settings = get_settings()
    order = await checkout_internal_order(
        settings.django_api_base_url,
        _internal_token(),
        telegram_user_id=callback.from_user.id,
        recipient_name=recipient_name,
        phone_number=phone,
        delivery_address=delivery_address,
        delivery_comment="",
    )
    await state.clear()
    if order is None:
        await callback.answer("Failed to create order", show_alert=True)
        return

    order_id = int(order.get("id") or 0)
    await callback.message.edit_text(
        f"Order #{order_id} created.\nPayment link: (stub)\nPress the button after payment.",
        reply_markup=order_paid_keyboard(order_id),
    )
    await callback.answer("Order created")


@router.callback_query(OrderPaidCallback.filter())
async def handle_order_paid(callback: CallbackQuery, callback_data: OrderPaidCallback) -> None:
    settings = get_settings()
    order = await mark_internal_order_paid(settings.django_api_base_url, _internal_token(), callback_data.order_id)
    if order is None:
        await callback.answer("Failed to mark paid", show_alert=True)
        return
    await callback.answer("Payment marked as paid")
    if callback.message is not None:
        await callback.message.edit_text(
            f"Order #{callback_data.order_id}: payment marked as paid.",
        )


@router.callback_query(CartAddCallback.filter())
async def handle_cart_add(callback: CallbackQuery, callback_data: CartAddCallback) -> None:
    if callback.from_user is None:
        await callback.answer("Cannot identify user", show_alert=True)
        return
    settings = get_settings()
    await add_internal_basket_item(
        settings.django_api_base_url,
        _internal_token(),
        telegram_user_id=callback.from_user.id,
        product_id=callback_data.product_id,
        quantity=1,
    )
    await callback.answer("Added to cart")
