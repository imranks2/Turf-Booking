# CLAUDE QUICK REF — Turf SaaS

## One-Liner
Multi-tenant turf booking SaaS for India. React 19 + Flask + MySQL + Razorpay + WhatsApp.

## Stack at a Glance
Frontend: React 19, TS 5.5, Tailwind 3.4, Vite, Zustand, TanStack Query v5, Recharts, Socket.io-client 4.7
Backend: Python 3.12, Flask 3, SQLAlchemy 2, Alembic, PyJWT, bcrypt, Pydantic v2
Infra: MySQL 8, Redis 7, Celery 5, AWS S3, Razorpay + RazorpayX, 2Factor/Gupshup WhatsApp

## Roles
saas_admin: Full platform. Manages owners, global analytics, payouts.
turf_owner: Manages turfs/sports/slots. Sees own analytics. Gets payouts.
player: Books turfs. Pays advance deposit + convenience fee.

## Pricing
₹40/hour total. ₹20 player convenience fee. ₹20 owner service fee.
Owner payout = (slot_price × hours) - ₹20/hour.

## Refund Rules
>24h: 100% advance. 12-24h: 50% advance. <12h: 0%. Platform fee never refunded.

## Key Flows
1. Player discovers turf → views calendar → selects slots → 5min Redis lock → Razorpay checkout → webhook confirms → slots booked → WhatsApp sent.
2. Owner blocks slot → DB update + Socket.io emit → players see slot removed.
3. Admin approves owner → owner adds bank → RazorpayX fund account created → payouts enabled.

## DB Core
users(id, email, phone, role, is_active)
turfs(id, tenant_id, name, city, amenities(JSON), operating_hours(JSON), images(JSON))
sports(id, tenant_id, name)
turf_sports(id, tenant_id, turf_id, sport_id, price_per_hour, advance_deposit_percentage)
slots(id, tenant_id, turf_sport_id, slot_date, start_time, end_time, status, booking_id)
bookings(id, tenant_id, booking_code, player_id, turf_sport_id, slot_ids(JSON), total_amount, advance_deposit_amount, platform_fee, owner_payout_amount, status, razorpay_order_id, razorpay_payment_id)
payments(id, tenant_id, booking_id, amount, type, razorpay_order_id, razorpay_payment_id, razorpay_transfer_id, status)

## API Prefix
/api/v1

## Socket.io Rooms
turf_{turf_id}, slot_{turf_sport_id}_{date}, user_{user_id}

## Redis Keys
refresh_token:{hash} (7d), slot_lock:{slot_id} (300s), processed:{payment_id} (24h), rate_limit:{ip|user_id} (60s)

## File Structure (Must Follow)
backend/app/{models,schemas,services,controllers,middleware,tasks,utils,websocket}
frontend/src/{components/{ui,layout,calendar,booking,turf,analytics},hooks,contexts,services,stores,types,utils,pages/{admin,owner,player}}

## Code Rules
- No explanatory comments. Self-documenting code only.
- No `any` in TypeScript. Strict mode.
- SQLAlchemy 2.0 style only. No raw SQL.
- Pydantic v2 for all validation.
- Named exports only. No default exports.
- Service layer contains all business logic. Controllers are thin.
- Custom exceptions + HTTP status codes.
- Alembic for all migrations.
- `__init__.py` in every Python package.

## Implementation Order
1. DB models + migrations + Flask scaffold + Auth
2. Turf CRUD + S3 + Slot generation
3. Player discovery + Calendar + Socket.io + Redis locks
4. Razorpay booking flow + Webhooks
5. Cancellation/Refunds + WhatsApp + Slot blocker
6. RazorpayX payouts + Analytics + Admin dashboard
7. Testing + Security + Mobile
8. Deploy

## Testing
pytest (unit + integration), Playwright (e2e), Locust (load/concurrency).

## Deployment
Ubuntu 22.04 VPS. Nginx → Gunicorn (Uvicorn worker). MySQL. Redis. Celery workers. SSL.
