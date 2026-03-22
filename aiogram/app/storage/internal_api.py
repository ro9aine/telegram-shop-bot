from __future__ import annotations

import asyncio
import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
BotSettingsPayload = dict[str, int | str | None]
_BOT_SETTINGS_CACHE: BotSettingsPayload | None = None
_BOT_SETTINGS_CACHE_EXPIRES_AT = 0.0


def request_json(
    *,
    url: str,
    internal_api_token: str | None,
    method: str = "GET",
    payload: dict | None = None,
    timeout: int = 8,
) -> dict | None:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, method=method, headers=headers)
    if internal_api_token:
        request.add_header("X-Internal-Token", internal_api_token)
    try:
        with urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else {}
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Internal API request failed method=%s url=%s error=%s", method, url, exc)
        return None


async def load_bot_settings(base_url: str, internal_api_token: str | None, cache_ttl: int) -> BotSettingsPayload | None:
    global _BOT_SETTINGS_CACHE, _BOT_SETTINGS_CACHE_EXPIRES_AT
    now = time.monotonic()
    if _BOT_SETTINGS_CACHE is not None and now < _BOT_SETTINGS_CACHE_EXPIRES_AT:
        return _BOT_SETTINGS_CACHE

    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/bot-settings/",
        internal_api_token=internal_api_token,
    )
    if payload is None:
        return None
    _BOT_SETTINGS_CACHE = {
        "admin_chat_id": payload.get("admin_chat_id"),
        "admin_telegram_ids": payload.get("admin_telegram_ids"),
    }
    _BOT_SETTINGS_CACHE_EXPIRES_AT = now + max(1, cache_ttl)
    return _BOT_SETTINGS_CACHE


async def load_active_orders(base_url: str, internal_api_token: str | None) -> list[dict]:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/orders/active/",
        internal_api_token=internal_api_token,
    )
    if not payload:
        return []
    items = payload.get("orders", [])
    return items if isinstance(items, list) else []


async def set_order_status(base_url: str, internal_api_token: str | None, order_id: int, status: str) -> bool:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/orders/{order_id}/status/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={"status": status},
    )
    return payload is not None


async def search_faq(base_url: str, internal_api_token: str | None, query: str, limit: int = 10) -> list[dict]:
    qs = urlencode({"q": query, "limit": str(limit)})
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/faq/search/?{qs}",
        internal_api_token=internal_api_token,
    )
    if not payload:
        return []
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


async def load_next_broadcast(base_url: str, internal_api_token: str | None) -> dict | None:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/broadcasts/next/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={},
    )
    if not payload:
        return None
    return payload.get("broadcast")


async def mark_broadcast_complete(
    base_url: str,
    internal_api_token: str | None,
    *,
    broadcast_id: int,
    delivered_count: int,
    failed_count: int,
) -> bool:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/broadcasts/{broadcast_id}/complete/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={"delivered_count": delivered_count, "failed_count": failed_count},
    )
    return payload is not None


async def load_internal_basket(base_url: str, internal_api_token: str | None, telegram_user_id: int) -> list[dict]:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/basket/{telegram_user_id}/",
        internal_api_token=internal_api_token,
    )
    if not payload:
        return []
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


async def add_internal_basket_item(
    base_url: str,
    internal_api_token: str | None,
    *,
    telegram_user_id: int,
    product_id: int,
    quantity: int = 1,
) -> list[dict]:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/basket/{telegram_user_id}/items/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={"product_id": product_id, "quantity": quantity},
    )
    if not payload:
        return []
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


async def update_internal_basket_item(
    base_url: str,
    internal_api_token: str | None,
    *,
    telegram_user_id: int,
    product_id: int,
    quantity: int,
) -> list[dict]:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/basket/{telegram_user_id}/items/{product_id}/",
        internal_api_token=internal_api_token,
        method="PATCH",
        payload={"quantity": quantity},
    )
    if not payload:
        return []
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


async def remove_internal_basket_item(
    base_url: str,
    internal_api_token: str | None,
    *,
    telegram_user_id: int,
    product_id: int,
) -> list[dict]:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/basket/{telegram_user_id}/items/{product_id}/",
        internal_api_token=internal_api_token,
        method="DELETE",
    )
    if not payload:
        return []
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


async def clear_internal_basket(base_url: str, internal_api_token: str | None, telegram_user_id: int) -> list[dict]:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/basket/{telegram_user_id}/clear/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={},
    )
    if not payload:
        return []
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


async def checkout_internal_order(
    base_url: str,
    internal_api_token: str | None,
    *,
    telegram_user_id: int,
    recipient_name: str,
    phone_number: str,
    delivery_address: str,
    delivery_comment: str = "",
) -> dict | None:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/orders/checkout/{telegram_user_id}/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={
            "recipient_name": recipient_name,
            "phone_number": phone_number,
            "delivery_address": delivery_address,
            "delivery_comment": delivery_comment,
        },
    )
    if not payload:
        return None
    order = payload.get("order")
    return order if isinstance(order, dict) else None


async def mark_internal_order_paid(base_url: str, internal_api_token: str | None, order_id: int) -> dict | None:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/internal/orders/{order_id}/mark-paid/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={},
    )
    if not payload:
        return None
    order = payload.get("order")
    return order if isinstance(order, dict) else None
