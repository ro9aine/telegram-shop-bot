import asyncio
from app.storage.internal_api import request_json


async def load_categories(base_url: str) -> list[dict]:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/api/catalog/categories/",
        internal_api_token=None,
        timeout=5,
    )
    if not payload:
        return []
    categories = payload.get("categories", [])
    if not isinstance(categories, list):
        return []
    return categories


async def load_products(base_url: str, category_id: int, page: int, page_size: int = 5) -> dict:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/api/catalog/products/?category_id={category_id}&page={page}&page_size={page_size}",
        internal_api_token=None,
        timeout=5,
    )
    if not payload:
        return {"items": [], "pagination": {"page": 1, "total_pages": 1}}
    return payload


async def load_product(base_url: str, product_id: int) -> dict | None:
    payload = await asyncio.to_thread(
        request_json,
        url=f"{base_url.rstrip('/')}/api/catalog/products/{product_id}/",
        internal_api_token=None,
        timeout=5,
    )
    if not payload:
        return None
    item = payload.get("item")
    return item if isinstance(item, dict) else None
