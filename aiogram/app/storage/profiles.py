import json
import logging
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

PROFILE_STORE_PATH = Path(__file__).resolve().parent.parent.parent / "profiles.json"


def load_profiles() -> dict[str, dict[str, str]]:
    if not PROFILE_STORE_PATH.exists():
        return {}

    with PROFILE_STORE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_profiles(profiles: dict[str, dict[str, str]]) -> None:
    with PROFILE_STORE_PATH.open("w", encoding="utf-8") as file:
        json.dump(profiles, file, ensure_ascii=False, indent=2)


def get_profile(user_id: int) -> dict[str, str] | None:
    return load_profiles().get(str(user_id))


def save_profile(user_id: int, phone_number: str) -> None:
    profiles = load_profiles()
    profiles[str(user_id)] = {"phone_number": phone_number}
    save_profiles(profiles)


def sync_profile(
    *,
    base_url: str,
    internal_api_token: str | None,
    telegram_user_id: int,
    phone_number: str,
    username: str,
    first_name: str,
    last_name: str,
) -> bool:
    payload = json.dumps(
        {
            "telegram_user_id": telegram_user_id,
            "phone_number": phone_number,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }
    ).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/internal/register-profile/",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    if internal_api_token:
        request.add_header("X-Internal-Token", internal_api_token)

    try:
        with urlopen(request, timeout=5):
            return True
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.warning("Failed to sync profile to Django: %s", exc)
        return False
