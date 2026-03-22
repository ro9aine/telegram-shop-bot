# Django Service

Backend and admin panel service.

Responsibilities:

- stores catalog, profiles, basket, orders, FAQ, broadcasts, required channels
- provides public API for WebApp (`/api/...`)
- provides internal API for bot (`/internal/...`) guarded by `X-Internal-Token`
- sends Telegram notifications on order updates/new orders

## Run in Docker

This service is started by root `docker-compose.yml` with migrations.

## Local Run

```bash
pip install -r requirements.txt
python shop/manage.py migrate
python shop/manage.py runserver 0.0.0.0:8000
```

## Admin

`http://localhost:8000/admin/`

## Config

Loaded from env (`shop/settings.py`). Main vars:

- `POSTGRES_*`
- `INTERNAL_API_TOKEN`
- `TELEGRAM_BOT_TOKEN` or `BOT_TOKEN`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CORS_ALLOWED_ORIGINS`, `DJANGO_CORS_ALLOW_ALL_ORIGINS`
- `TELEGRAM_INIT_DATA_MAX_AGE_SECONDS`
