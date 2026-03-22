# Telegram Shop Bot

Monorepo with 3 services:

- `aiogram`: Telegram bot (Aiogram 3)
- `djg`: Django backend + admin panel + PostgreSQL models
- `next`: Telegram WebApp (Next.js 15 + React 19)

All business data is stored in Django. Bot and WebApp use Django HTTP APIs.

## Services and Ports

- `postgres`: PostgreSQL 16 (`localhost:5432`)
- `djg`: Django (`http://localhost:8000`)
- `next`: WebApp (`http://localhost:3000`)
- `aiogram`: long-polling bot worker

## Quick Start

1. Create `.env` from the template:

```bash
cp .env.example .env
```

2. Fill required secrets in `.env`:

- `BOT_TOKEN`
- `NEXT_PUBLIC_BOT_USERNAME` (or `BOT_USERNAME`)
- `INTERNAL_API_TOKEN`

3. Start all services:

```bash
docker compose up --build
```

4. Create Django superuser:

```bash
docker compose exec djg python shop/manage.py createsuperuser
```

5. Open Django admin:

- `http://localhost:8000/admin/`
- Configure required channels, catalog, FAQ, broadcasts, and bot settings.

## Environment Variables

See `.env.example` for full list.

Important variables:

- `BOT_TOKEN`, `BOT_USERNAME`, `NEXT_PUBLIC_BOT_USERNAME`
- `INTERNAL_API_TOKEN`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `DJANGO_API_BASE_URL`, `CATALOG_API_BASE_URL`, `NEXT_PUBLIC_CATALOG_API_BASE_URL`
- `WEBAPP_CATALOG_URL`
- `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`, `DJANGO_CORS_ALLOW_ALL_ORIGINS`
- `TELEGRAM_INIT_DATA_MAX_AGE_SECONDS`
- `NEXT_ALLOWED_DEV_ORIGINS`

## What Is Implemented

- Registration via `/start` and contact sharing
- Required channel subscription checks (from Django admin config)
- Catalog browsing, deep links (`/start product_<id>`), product cards
- Basket management and checkout flow
- Order status updates and admin-chat notifications
- FAQ inline query search
- Broadcast queue processing by bot worker
- Telegram WebApp integration with `initData` forwarding/validation

## Logs

- Bot logs: `aiogram/logs/bot.log`
- Django logs: `djg/shop/logs/django.log`

## Notes

- Django migrations run automatically when `djg` container starts.
- Python services are built from `requirements.txt`.
- `pyproject.toml` is kept aligned for local Poetry-based workflows.
