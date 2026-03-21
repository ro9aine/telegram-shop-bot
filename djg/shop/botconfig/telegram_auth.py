import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


@dataclass(frozen=True)
class TelegramWebAppAuth:
    user_id: int
    auth_date: int


def validate_telegram_init_data(
    *,
    init_data: str,
    bot_token: str,
    max_age_seconds: int,
) -> TelegramWebAppAuth | None:
    init_data = (init_data or "").strip()
    bot_token = (bot_token or "").strip()
    if not init_data or not bot_token:
        return None

    pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
    data: dict[str, str] = {}
    received_hash = ""
    for key, value in pairs:
        if key == "hash":
            received_hash = value
            continue
        data[key] = value

    if not received_hash:
        return None

    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data.keys()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    raw_auth_date = data.get("auth_date", "")
    try:
        auth_date = int(raw_auth_date)
    except ValueError:
        return None
    if max_age_seconds > 0 and (int(time.time()) - auth_date) > max_age_seconds:
        return None

    raw_user = data.get("user", "")
    if not raw_user:
        return None
    try:
        user_payload = json.loads(raw_user)
    except json.JSONDecodeError:
        return None

    user_id_raw = user_payload.get("id")
    if not isinstance(user_id_raw, int):
        return None

    return TelegramWebAppAuth(user_id=user_id_raw, auth_date=auth_date)
