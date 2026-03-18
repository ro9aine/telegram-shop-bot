from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


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
