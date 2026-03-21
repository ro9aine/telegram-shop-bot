# Telegram Shop Bot

Three-service project:

1. `aiogram` bot (Aiogram 3)
2. `djg` admin/backend (Django)
3. `next` WebApp (Next.js/TypeScript)

Services communicate through HTTP APIs exposed by Django.

## Architecture

- Django stores catalog, users, basket, orders, FAQ, broadcasts, and bot settings.
- Aiogram uses Django APIs:
  - public API (`/api/...`) for WebApp-compatible data contracts
  - internal API (`/internal/...`) protected by `X-Internal-Token`
- Next.js WebApp talks to Django API and validates Telegram `initData`.

Why this approach:

- single source of truth for business data (Django/PostgreSQL)
- bot and WebApp share basket/orders consistently
- no direct DB access from bot/frontend

## Implemented Features

- Registration by `/start` + `request_contact=True`
- Required channel subscription middleware (dynamic list from admin)
- Catalog with categories/subcategories, pagination, product cards, MediaGroup
- Deep linking: `t.me/<bot>?start=product_<id>` and `t.me/<bot>?start=<id>`
- Bot cart:
  - list items
  - quantity `+/-`
  - remove
  - clear
  - checkout entry
- FSM checkout in bot: recipient -> address -> confirm
- Payment stub + `Я оплатил(а)` button (marks order payment status as paid)
- Order status notifications to user on admin status change
- Admin chat:
  - auto notification for new orders
  - inline status buttons
  - `/admin_orders` command for active orders
- FAQ inline query (`InlineQueryResultArticle`)
- Broadcast queue from admin, sent by bot in background
- Bot commands registration via `set_my_commands`
- Custom middlewares:
  - subscription check
  - registration sync/injection
  - update logging
- Custom filter: `IsAdmin`
- Admin:
  - catalog CRUD (+ multiple product images)
  - customers and orders
  - FAQ CRUD
  - broadcasts with statuses and delivery stats
  - bot settings (`admin_chat_id`)
  - paid orders export (CSV for Excel)
- Telegram WebApp integration:
  - backend `initData` validation
  - theme params support
  - Telegram Back/Main buttons usage

## Run

```bash
docker compose up --build
```

## Required Setup

1. Copy `.env.example` to `.env` and fill secrets.
2. Start stack with docker compose.
3. Create superuser:

```bash
docker compose exec djg python shop/manage.py createsuperuser
```

4. Open Django admin and configure:
   - required channels
   - bot settings (`admin_chat_id`)
   - catalog/FAQ/broadcasts

## Environment Variables

See `.env.example`.

Main variables:

- `BOT_TOKEN`
- `INTERNAL_API_TOKEN`
- `POSTGRES_*`
- `DJANGO_API_BASE_URL`
- `WEBAPP_CATALOG_URL`
- `NEXT_PUBLIC_BOT_USERNAME`
- `ADMIN_TELEGRAM_IDS`

## Notes

- Logs are written with rotation:
  - `aiogram/logs/bot.log`
  - `djg/shop/logs/django.log`
- DB migrations are applied on Django container start (`docker-compose` command).
