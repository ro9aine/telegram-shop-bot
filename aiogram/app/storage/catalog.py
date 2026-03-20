import asyncio
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def _fetch_json(url: str) -> dict | None:
    try:
        with urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load catalog data from %s: %s", url, exc)
        return None


async def load_categories(base_url: str) -> list[dict]:
    payload = await asyncio.to_thread(_fetch_json, f"{base_url.rstrip('/')}/api/catalog/categories/")
    if not payload:
        return []
    categories = payload.get("categories", [])
    if not isinstance(categories, list):
        return []
    return categories


async def load_products(base_url: str, category_id: int, page: int, page_size: int = 5) -> dict:
    payload = await asyncio.to_thread(
        _fetch_json,
        f"{base_url.rstrip('/')}/api/catalog/products/?category_id={category_id}&page={page}&page_size={page_size}",
    )
    if not payload:
        return {"items": [], "pagination": {"page": 1, "total_pages": 1}}
    return payload


async def load_product(base_url: str, product_id: int) -> dict | None:
    payload = await asyncio.to_thread(
        _fetch_json,
        f"{base_url.rstrip('/')}/api/catalog/products/{product_id}/",
    )
    if not payload:
        return None
    item = payload.get("item")
    return item if isinstance(item, dict) else None
