from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: SecretStr
    django_api_base_url: str = "http://127.0.0.1:8000"
    webapp_catalog_url: str = ""
    internal_api_token: SecretStr | None = None
    required_channels_cache_ttl: int = 30
    admin_telegram_ids: str = ""
    bot_settings_cache_ttl: int = 30
    broadcast_poll_interval_seconds: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
