import asyncio
import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
_CACHE: list[dict[str, str]] = []
_CACHE_EXPIRES_AT = 0.0


def _fetch_required_channels(base_url: str, internal_api_token: str | None) -> list[dict[str, str]] | None:
    request = Request(f"{base_url.rstrip('/')}/internal/required-channels/")
    if internal_api_token:
        request.add_header("X-Internal-Token", internal_api_token)

    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.warning("Failed to fetch required channels: %s", exc)
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
