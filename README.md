# Turf SaaS Platform

Multi-tenant turf management & booking SaaS for India. React 19 + Flask 3 + MySQL 8 + Redis 7 + Razorpay + WhatsApp.

## Stack
- **Frontend**: React 19, TypeScript 5.5, Tailwind 3.4, Vite, TanStack Query v5, Zustand, Recharts, Socket.io-client
- **Backend**: Python 3.12, Flask 3, SQLAlchemy 2.0, Alembic, PyJWT, bcrypt, Pydantic v2
- **Infra**: MySQL 8, Redis 7, Celery 5, AWS S3, Razorpay + RazorpayX, 2Factor/Gupshup WhatsApp

## Roles
- `saas_admin` — platform admin: owner approval, global analytics, payout queue
- `turf_owner` — manages turfs/sports/slots, receives payouts (tenant-isolated)
- `player` — discovers turfs, books slots, pays advance + convenience fee

## Repository layout
```
backend/    Flask app, SQLAlchemy models, Celery tasks, Alembic migrations, tests
frontend/   Vite + React app, Playwright e2e
systemd/    turf-backend.service, turf-celery.service
nginx.conf  Host reverse-proxy (Gunicorn unix socket + SPA + ws)
docker-compose.yml
scripts/deploy.sh
```

## Local development
### Backend
```bash
cd backend
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in secrets
alembic upgrade head            # against your MySQL 8
python wsgi.py                  # dev server (Socket.IO on :5000)
celery -A celery_worker.celery worker -l info -Q whatsapp,payouts,refunds,default
pytest                          # unit + integration (sqlite)
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev                     # Vite on :5173, proxies /api + /socket.io to :5000
npm run typecheck && npm run build
npm run test:e2e                # Playwright (requires app + backend running)
```

## Demo data (seed)
Idempotent seed script — safe to re-run. Creates an admin, two turf owners (with turfs, sports, 14 days of slots), a player, and one confirmed demo booking.

```bash
# local
cd backend && python seed.py
# docker
docker compose exec backend python seed.py
```

| Role | Email | Password |
|------|-------|----------|
| saas_admin | admin@turfapp.in | `Admin@12345` |
| turf_owner | owner1@turfapp.in | `Owner@12345` |
| turf_owner | owner2@turfapp.in | `Owner@12345` |
| player | player@turfapp.in | `Player@12345` |

## Docker (single host)
```bash
cp backend/.env.example backend/.env   # fill secrets; DATABASE_URL points at db service
docker compose up -d --build
# backend runs `alembic upgrade head` on start; frontend served by nginx on :80
```

## VPS deployment (Ubuntu 22.04)
1. Install Nginx, MySQL 8, Redis 7, Python 3.12, Node 20. Create `turf` user; clone to `/opt/turf`.
2. `backend/.env` with production secrets (`FLASK_ENV=production`).
3. `cp systemd/*.service /etc/systemd/system/ && systemctl enable --now turf-backend turf-celery`.
4. `cp nginx.conf /etc/nginx/sites-available/turf && ln -s ... /etc/nginx/sites-enabled/`.
5. SSL: `certbot --nginx -d turfapp.in -d www.turfapp.in`.
6. `bash scripts/deploy.sh` for subsequent releases.
7. Firewall: allow 80, 443, 22 only.
8. Razorpay webhook → `https://turfapp.in/api/v1/webhooks/razorpay`; WhatsApp callbacks → `/api/v1/webhooks/whatsapp`.

## Payment model
₹40/hr platform fee (₹20 player convenience + ₹20 owner service). Owner payout = `slot_price × hours − ₹20 × hours`.
Refunds: >24h 100% advance, 12–24h 50%, <12h 0%; convenience fee never refunded.

## Notes
- Gunicorn uses the **GeventWebSocket worker** (Flask-SocketIO is WSGI; the UvicornWorker in the original checklist is ASGI-only and won't serve this app).
- Tests run against SQLite; production targets MySQL 8. The initial migration (`0001_initial`) bootstraps the schema from the SQLAlchemy metadata — generate future migrations with `alembic revision --autogenerate`.
