# Aiogram Service

Telegram bot service for customer interactions:

- registration (`/start` + contact)
- catalog and product actions
- basket and checkout actions
- admin commands and notifications
- background broadcast delivery worker

## Run in Docker

This service is started by root `docker-compose.yml`.

## Local Run

```bash
pip install -r requirements.txt
python -m app.main
```

Dev autoreload entrypoint:

```bash
python -m app.dev
```

## Config

Uses env vars from root `.env` through `app/config.py` (`pydantic-settings`).

Important vars:

- `BOT_TOKEN`
- `DJANGO_API_BASE_URL`
- `INTERNAL_API_TOKEN`
- `WEBAPP_CATALOG_URL`
- `REQUIRED_CHANNELS_CACHE_TTL`
- `BOT_SETTINGS_CACHE_TTL`
- `BROADCAST_POLL_INTERVAL_SECONDS`
