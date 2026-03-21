from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from urllib.parse import urlparse, urlunparse

from app.callbacks import (
    CatalogBackCallback,
    CatalogCategoryCallback,
    CatalogPageCallback,
    CatalogProductCallback,
    CartAddCallback,
    CartChangeQtyCallback,
    CartCheckoutCallback,
    CartClearCallback,
    CartRemoveCallback,
    CheckoutFlowCallback,
    OrderPaidCallback,
)


def _webapp_button(url: str) -> InlineKeyboardButton | None:
    parsed = urlparse((url or "").strip())
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    return InlineKeyboardButton(text="Open in WebApp", web_app=WebAppInfo(url=url))


def webapp_only_keyboard(url: str, text: str = "Open in WebApp") -> InlineKeyboardMarkup | None:
    button = _webapp_button(url)
    if button is None:
        return None
    button.text = text
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def _build_product_url(url: str, product_id: int) -> str:
    parsed = urlparse(url)
    base_path = (parsed.path or "").rstrip("/")
    product_path = f"{base_path}/product/{product_id}"
    return urlunparse(parsed._replace(path=product_path))


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Share contact", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def subscription_prompt(channels: list[dict[str, str]]) -> InlineKeyboardMarkup | None:
    buttons = []
    for channel in channels:
        invite_link = channel["invite_link"]
        if invite_link:
            buttons.append([InlineKeyboardButton(text=channel["title"], url=invite_link)])

    if not buttons:
        return None

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def catalog_categories_keyboard(
    categories: list[dict],
    webapp_url: str,
    parent_id: int | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for category in categories:
        rows.append(
            [
                InlineKeyboardButton(
                    text=category["title"],
                    callback_data=CatalogCategoryCallback(category_id=category["id"]).pack(),
                )
            ]
        )

    if parent_id is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Back",
                    callback_data=CatalogBackCallback(parent_id=parent_id).pack(),
                )
            ]
        )

    webapp_btn = _webapp_button(webapp_url)
    if webapp_btn is not None:
        rows.append([webapp_btn])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def catalog_products_keyboard(
    *,
    products: list[dict],
    category_id: int,
    page: int,
    total_pages: int,
    parent_id: int | None,
    webapp_url: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for product in products:
        rows.append(
            [
                InlineKeyboardButton(
                    text=product["title"],
                    callback_data=CatalogProductCallback(
                        product_id=product["id"],
                        category_id=category_id,
                        page=page,
                    ).pack(),
                )
            ]
        )

    pagination_row: list[InlineKeyboardButton] = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="Back",
                callback_data=CatalogPageCallback(category_id=category_id, page=page - 1).pack(),
            )
        )
    if page < total_pages:
        pagination_row.append(
            InlineKeyboardButton(
                text="Forward",
                callback_data=CatalogPageCallback(category_id=category_id, page=page + 1).pack(),
            )
        )
    if pagination_row:
        rows.append(pagination_row)

    rows.append(
        [
            InlineKeyboardButton(
                text="To categories",
                callback_data=CatalogBackCallback(parent_id=parent_id or 0).pack(),
            )
        ]
    )
    webapp_btn = _webapp_button(webapp_url)
    if webapp_btn is not None:
        rows.append([webapp_btn])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_card_keyboard(
    *,
    product_id: int,
    category_id: int | None,
    page: int | None,
    webapp_url: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="Add to cart", callback_data=CartAddCallback(product_id=product_id).pack())],
    ]
    if category_id is not None and page is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Back to products",
                    callback_data=CatalogPageCallback(category_id=category_id, page=page).pack(),
                )
            ]
        )
    webapp_btn = _webapp_button(_build_product_url(webapp_url, product_id))
    if webapp_btn is not None:
        rows.append([webapp_btn])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def cart_item_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="-",
                    callback_data=CartChangeQtyCallback(product_id=product_id, delta=-1).pack(),
                ),
                InlineKeyboardButton(
                    text="+",
                    callback_data=CartChangeQtyCallback(product_id=product_id, delta=1).pack(),
                ),
                InlineKeyboardButton(
                    text="Remove",
                    callback_data=CartRemoveCallback(product_id=product_id).pack(),
                ),
            ]
        ]
    )


def cart_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Clear cart",
                    callback_data=CartClearCallback(confirm=1).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Checkout",
                    callback_data=CartCheckoutCallback(start=1).pack(),
                )
            ],
        ]
    )


def order_paid_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Я оплатил(а)", callback_data=OrderPaidCallback(order_id=order_id).pack())]
        ]
    )


def checkout_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Confirm order",
                    callback_data=CheckoutFlowCallback(action="confirm").pack(),
                ),
                InlineKeyboardButton(
                    text="Cancel",
                    callback_data=CheckoutFlowCallback(action="cancel").pack(),
                ),
            ]
        ]
    )
