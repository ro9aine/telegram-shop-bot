# Next WebApp Service

Telegram WebApp frontend (Next.js 15 + React 19).

## Run in Docker

This service is started by root `docker-compose.yml`.

## Local Run

```bash
npm install
npm run dev
```

## Config

Main env vars:

- `CATALOG_API_BASE_URL` (server-side backend proxy target)
- `NEXT_PUBLIC_CATALOG_API_BASE_URL` (browser fallback)
- `NEXT_PUBLIC_BOT_USERNAME`
- `NEXT_ALLOWED_DEV_ORIGINS`

## API Proxy

Route handler `app/api/backend/[...path]/route.ts` forwards requests to Django API and preserves request method/body/headers (except hop-by-hop headers).
