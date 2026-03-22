import json
from pathlib import Path

from app.storage.internal_api import request_json

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
    photo_url: str = "",
) -> bool:
    payload = request_json(
        url=f"{base_url.rstrip('/')}/internal/register-profile/",
        internal_api_token=internal_api_token,
        method="POST",
        payload={
            "telegram_user_id": telegram_user_id,
            "phone_number": phone_number,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "photo_url": photo_url,
        },
        timeout=5,
    )
    return payload is not None
