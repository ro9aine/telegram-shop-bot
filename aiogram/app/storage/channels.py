import asyncio
import time

from app.storage.internal_api import request_json

_CACHE: list[dict[str, str]] = []
_CACHE_EXPIRES_AT = 0.0


def _fetch_required_channels(base_url: str, internal_api_token: str | None) -> list[dict[str, str]] | None:
    payload = request_json(
        url=f"{base_url.rstrip('/')}/internal/required-channels/",
        internal_api_token=internal_api_token,
        timeout=5,
    )
    if payload is None:
        return None

    return payload.get("channels", [])


async def load_required_channels(
    base_url: str,
    internal_api_token: str | None,
    cache_ttl: int,
) -> list[dict[str, str]] | None:
    global _CACHE, _CACHE_EXPIRES_AT

    now = time.monotonic()
    if now < _CACHE_EXPIRES_AT:
        return _CACHE

    channels = await asyncio.to_thread(_fetch_required_channels, base_url, internal_api_token)
    if channels is None:
        return None

    _CACHE = channels
    _CACHE_EXPIRES_AT = now + max(cache_ttl, 1)
    return _CACHE
