# CLAUDE.md — Turf SaaS Platform

## Role
You are a senior full-stack engineer building a multi-tenant Turf Management & Booking SaaS. You write production-grade code. You do not explain what you are doing unless explicitly asked. You write code, configs, and tests only.

## Absolute Rules
- NEVER add explanatory comments like "This function does X". Code must be self-documenting.
- NEVER apologize, disclaim, or summarize. Just output files.
- ALWAYS use the exact versions specified below. No alternatives.
- ALWAYS follow the file structure. Do not create extra directories.
- ALWAYS write TypeScript with strict mode. No `any`.
- ALWAYS use SQLAlchemy 2.0 style (declarative mapping, `session.get()`, `select()`).
- ALWAYS validate inputs with Pydantic v2.
- ALWAYS handle errors with custom exception classes and HTTP status codes.
- NEVER commit secrets to code. Use `.env` and `pydantic-settings`.
- NEVER use raw SQL. ORM only.
- ALWAYS include `__init__.py` in Python packages.
- ALWAYS add indexes to foreign keys and query columns.

## Tech Stack (latest, verified working — pinned in requirements.txt / package.json)
| Layer | Spec |
|-------|------|
| Frontend | React 19.2, TypeScript 6.0, Tailwind CSS 3.4, Vite 8, React Router 6, Zustand 5, TanStack Query v5, Recharts 2, Socket.io-client 4.8 |
| Backend | Python 3.12, Flask 3.1, Flask-SocketIO 5.6, Flask-CORS 6.0, Gunicorn 26, Uvicorn 0.49 |
| Database | MySQL 8.0, SQLAlchemy 2.0.51, Alembic 1.18, PyMySQL 1.2 |
| Auth | PyJWT 2.13, bcrypt 5.0, python-jose 3.5 |
| Real-time | Socket.io 4.8 + Redis adapter |
| Payments | Razorpay Python 2.0.1, RazorpayX Payouts API |
| Notifications | 2Factor / Gupshup REST APIs |
| Storage | boto3 1.43, AWS S3 (ap-south-1) |
| Cache/Queue | Redis 8.0, Celery 5.6, Flower 2.0 |
| Validation | Pydantic 2.13, email-validator 2.3 |
| Testing | pytest 9.1, pytest-flask 1.3, Playwright 1.61 |
| Held at current major (next major = breaking migration) | Tailwind 3 (→4 CSS-first), Recharts 2 (→3), React Router 6 (→7), Zod 3 (→4) |

## Architecture
- **Multi-tenancy**: Shared database, shared schema. Every tenant-scoped table has `tenant_id` (UUID) column. SaaS Admin queries omit `tenant_id`. Turf Owner queries auto-filter `tenant_id = current_user.id`.
- **RBAC**: `saas_admin`, `turf_owner`, `player`. Middleware enforces roles. JWT payload contains `user_id`, `role`, `tenant_id` (if applicable).
- **API Style**: RESTful JSON. Base path `/api/v1`. Standard response envelope: `{success: bool, data: T, error?: {code, message}}`.
- **Stateless**: No server-side sessions. JWT access token (15min) + HTTP-only refresh cookie (7 days). Refresh token hash stored in Redis.
- **Async**: Celery for WhatsApp sends, refunds, payouts. Redis broker.
- **Real-time**: Socket.io rooms per `turf_{id}`, `slot_{turf_sport_id}_{date}`, `user_{id}`.

## Database Schema
Implement exactly these tables with SQLAlchemy models. Use UUID primary keys (CHAR(36)). Use `DateTime(timezone=True)`. Use JSON columns where specified. Add `created_at`, `updated_at` to every table.

```python
# Core
users: id, email, phone, password_hash, role(enum), is_active, is_verified, created_at, updated_at
saas_admin_profile: id, user_id(FK), name, permissions_json

turf_owner_profile: id, user_id(FK), business_name, gst_number, bank_account_number, bank_ifsc, razorpay_contact_id, razorpay_fund_account_id, payout_method, kyc_status(enum), subscription_status, subscription_expires_at, created_at, updated_at

players: id, user_id(FK), name, phone, city, preferred_sports(JSON), profile_image_url, created_at, updated_at

# Tenant-scoped (all have tenant_id FK -> users.id)
turfs: id, tenant_id, name, address, city, latitude, longitude, description, amenities(JSON), images(JSON), is_active, operating_hours(JSON), created_at, updated_at
sports: id, tenant_id, name, icon_url, default_duration_minutes, is_active
turf_sports: id, tenant_id, turf_id(FK), sport_id(FK), price_per_hour, advance_deposit_percentage, min_players, max_players, is_active
slots: id, tenant_id, turf_sport_id(FK), slot_date, start_time, end_time, status(enum: available, booked, blocked, maintenance), booking_id(FK, nullable), blocked_reason, created_at, updated_at

# Booking & Payments
bookings: id, tenant_id, booking_code, player_id(FK), turf_sport_id(FK), slot_ids(JSON), booking_date, total_amount, advance_deposit_amount, platform_fee, owner_payout_amount, status(enum: pending_payment, confirmed, cancelled, completed, no_show), payment_status, razorpay_order_id, razorpay_payment_id, cancellation_reason, cancelled_at, refund_status, refund_amount, razorpay_refund_id, created_at, updated_at

payments: id, tenant_id, booking_id(FK), amount, type(enum: advance, full, refund, payout), razorpay_order_id, razorpay_payment_id, razorpay_transfer_id, status, metadata_json, created_at, updated_at

slot_blocks: id, tenant_id, turf_sport_id(FK), slot_date, start_time, end_time, reason(enum: offline_walkin, maintenance, private_event, other), notes, created_by(FK), created_at, updated_at

notification_logs: id, tenant_id, recipient_phone, template_name, variables_json, provider(enum: 2factor, gupshup, twilio), status, response_json, sent_at, delivered_at

daily_analytics: id, date, total_bookings, total_revenue, total_platform_fees, total_owner_payouts, active_turfs, active_players, created_at

audit_logs: id, user_id(FK), action, entity_type, entity_id, old_values_json, new_values_json, ip_address, created_at
```

**Indexes**: 
- `slots`: composite on `(turf_sport_id, slot_date, status)`
- `bookings`: composite on `(player_id, status)`, `(tenant_id, created_at)`
- `users`: unique on `email`, `phone`
- `turfs`: index on `tenant_id`, `city`
- `payments`: index on `booking_id`, `razorpay_payment_id`

## API Endpoints
Implement exactly these. All protected routes require JWT in `Authorization: Bearer <token>`.

**Auth** (`/api/v1/auth`)
- `POST /register` — body: `{email, phone, password, role, name, business_name?}`. If role=turf_owner, set `is_active=false` pending admin approval.
- `POST /login` — body: `{email, password}`. Returns `{access_token, user}` and sets refresh cookie.
- `POST /refresh` — reads refresh cookie. Returns new access token.
- `POST /logout` — blacklists refresh token in Redis.
- `POST /forgot-password` — sends email with 1h reset token (Redis).
- `POST /reset-password` — body: `{token, new_password}`.

**SaaS Admin** (`/api/v1/admin`) — `require_role(['saas_admin'])`
- `GET /users?q=&role=&status=&page=&limit=` — list all users.
- `PATCH /users/:id/approve` — activate turf_owner, trigger welcome WhatsApp.
- `PATCH /users/:id/suspend` — deactivate account.
- `GET /analytics?from=&to=` — global KPIs + time-series.
- `GET /payouts?status=&page=&limit=` — payout queue.
- `POST /payouts/:id/retry` — retry failed payout via Celery.
- `GET /audit-logs?user_id=&action=&page=&limit=`

**Turf Owner** (`/api/v1/owner`) — `require_role(['turf_owner'])` + tenant isolation
- `GET /turfs` — list my turfs.
- `POST /turfs` — create turf. Handle S3 image upload (multipart/form-data, max 10 images, 5MB each, JPG/PNG).
- `PUT /turfs/:id` — update turf.
- `DELETE /turfs/:id` — soft delete (`is_active=false`).
- `GET /turfs/:id/sports`
- `POST /turfs/:id/sports` — add sport with pricing.
- `PUT /turfs/:id/sports/:sport_id`
- `GET /slots?turf_id=&sport_id=&date=` — return slots for calendar.
- `POST /slots/block` — body: `{turf_sport_id, slot_date, start_time, end_time, reason, notes}`. Sets `status=blocked`, emits Socket.io event, deletes any Redis locks.
- `POST /slots/unblock` — body: `{slot_id}`.
- `POST /slots/bulk-block` — body: `{turf_sport_id, start_date, end_date, days_of_week[], start_time, end_time, reason}`.
- `GET /bookings?turf_id=&status=&from=&to=&page=&limit=`
- `GET /bookings/:id`
- `POST /bookings/:id/no-show` — triggers partial refund if policy allows.
- `GET /analytics?from=&to=&group_by=` — revenue, bookings, sport breakdown.
- `GET /payouts`
- `PUT /profile/bank` — validate IFSC, create RazorpayX fund account.

**Player** (`/api/v1`) — public routes allowed without auth; booking requires auth
- `GET /turfs?city=&sport=&lat=&lng=&radius=&amenities[]=&date=&price_min=&price_max=&page=&limit=` — discovery.
- `GET /turfs/:id` — detail with sports.
- `GET /turfs/:id/slots?date=&sport_id=` — available slots only.
- `POST /bookings` — auth required. Body: `{turf_sport_id, slot_ids[], player_id}`. Server calculates total, creates Razorpay order for `advance_deposit + convenience_fee`, returns `{booking_id, razorpay_order_id, amount}`.
- `GET /bookings` — my bookings.
- `GET /bookings/:id`
- `POST /bookings/:id/cancel` — auth required. Applies refund rules, triggers Razorpay refund API, queues WhatsApp.
- `PUT /player/profile` — auth required.
- `POST /player/profile/image` — auth required. S3 upload.

**Webhooks** (no auth, signature verify)
- `POST /webhooks/razorpay` — verify `X-Razorpay-Signature` with HMAC. Idempotent via Redis `processed:{payment_id}`. Handle: `payment.captured`, `payment.failed`, `refund.processed`, `payout.processed`, `payout.failed`.
- `POST /webhooks/whatsapp` — delivery status callbacks.

**Public**
- `GET /sports`
- `GET /cities`

## Payment Logic (Razorpay)
1. **Order Creation**: `amount = (total_price * advance_deposit_percentage) + (₹20 * hours)` in paise.
2. **Split**: On `payment.captured`:
   - Platform fee = ₹40 * hours (₹20 from player + ₹20 from owner).
   - Owner payout = (total_price) - ₹20 * hours.
   - Create RazorpayX transfer to owner's fund account (queue via Celery if payout is T+1).
3. **Refund Rules** (hardcoded):
   - >24h before kickoff: 100% advance deposit refund.
   - 12-24h: 50% advance deposit refund.
   - <12h: 0% advance deposit refund.
   - Platform fee (₹20/hr) never refunded.
4. **Payouts**: RazorpayX Contact + Fund Account created during owner KYC. Payout queued via Celery. Retry on failure (max 3, exponential backoff).

## Real-Time / Socket.io
Server events:
- `join_turf_room` `{turf_id}` — add to room.
- `join_slot_room` `{turf_sport_id, date}` — add to room.
- `lock_slot` `{slot_id}` — Redis `SET slot_lock:{slot_id} {player_id} EX 300 NX`. Emit `slot_locked` to room. Reject if NX fails.
- `unlock_slot` `{slot_id}` — verify player_id matches, DEL, emit `slot_unlocked`.
- `block_slot` `{slot_id, reason}` — owner only. DB update, DEL lock, emit `slot_blocked`.

Client events:
- `slot_locked`, `slot_unlocked`, `slot_booked`, `slot_blocked`, `slot_available`, `booking_conflict`

## WhatsApp Templates (2Factor/Gupshup)
Use template-based API. Variables injected via Jinja2. All sends are async Celery tasks.

| Template | Variables |
|----------|-----------|
| `turf_booking_confirmed` | player_name, turf_name, sport, date, time, booking_code, address |
| `turf_kickoff_reminder` | player_name, turf_name, sport, time, booking_code |
| `turf_payment_failed` | player_name, turf_name, slot_time, retry_link |
| `turf_booking_cancelled` | player_name, turf_name, date, refund_amount, refund_days |
| `turf_refund_processed` | player_name, booking_code, refund_amount, transaction_id |
| `turf_owner_new_booking` | owner_name, player_name, sport, date, time, amount |
| `turf_owner_payout` | owner_name, amount, date, transaction_id |

## Frontend Structure
```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx                    # Router setup, route guards
│   ├── components/
│   │   ├── ui/                   # Button, Input, Card, Modal, Badge, Table (shadcn style)
│   │   ├── layout/               # Sidebar, TopNav, MobileNav, Footer
│   │   ├── calendar/             # CalendarGrid, SlotCell, TimeHeader, DatePicker
│   │   ├── booking/              # BookingFlow, PriceBreakdown, RazorpayCheckout, BookingCard
│   │   ├── turf/                 # TurfCard, TurfDetail, ImageGallery, AmenityTag
│   │   └── analytics/            # KpiCard, LineChart, BarChart, PieChart, DateRangePicker
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useSocket.ts         # SocketContext consumer
│   │   ├── useCalendar.ts       # Slot fetch + lock logic
│   │   ├── useBookings.ts       # TanStack Query hooks
│   │   └── useOwnerTurfs.ts
│   ├── contexts/
│   │   ├── AuthContext.tsx       # Auth state, login/logout
│   │   └── SocketContext.tsx     # Socket.io connection, room management
│   ├── services/
│   │   ├── api.ts               # Axios instance, interceptors (refresh token), baseURL from env
│   │   ├── razorpay.ts          # Load Razorpay script, open checkout
│   │   └── socket.ts            # Socket.io client singleton
│   ├── stores/
│   │   └── appStore.ts          # Zustand: sidebarOpen, notifications, currentTurf
│   ├── types/
│   │   └── index.ts             # All interfaces: User, Turf, Sport, Slot, Booking, Payment
│   ├── utils/
│   │   ├── constants.ts         # Role enums, slot status, booking status
│   │   ├── formatters.ts        # Date, currency (INR), time formatters
│   │   └── validators.ts        # Zod schemas for forms
│   └── pages/
│       ├── admin/
│       │   ├── Dashboard.tsx
│       │   ├── Users.tsx
│       │   ├── Analytics.tsx
│       │   └── Payouts.tsx
│       ├── owner/
│       │   ├── Dashboard.tsx
│       │   ├── Turfs.tsx
│       │   ├── TurfForm.tsx
│       │   ├── Calendar.tsx
│       │   ├── Bookings.tsx
│       │   └── Analytics.tsx
│       └── player/
│           ├── Home.tsx         # Discovery
│           ├── TurfDetail.tsx
│           ├── BookingConfirm.tsx
│           ├── MyBookings.tsx
│           └── Profile.tsx
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Backend Structure
```
backend/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py               # Pydantic-settings, env vars
│   ├── extensions.py           # db, socketio, celery, redis, jwt, bcrypt, s3
│   ├── exceptions.py           # Custom exceptions + error handlers
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── turf.py
│   │   ├── sport.py
│   │   ├── slot.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   └── analytics.py
│   ├── schemas/                # Pydantic v2 request/response models
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── turf.py
│   │   ├── booking.py
│   │   └── payment.py
│   ├── services/               # Business logic (no HTTP here)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── turf_service.py
│   │   ├── booking_service.py
│   │   ├── payment_service.py
│   │   ├── razorpay_service.py
│   │   ├── whatsapp_service.py
│   │   └── analytics_service.py
│   ├── controllers/            # Flask blueprints (thin, delegate to services)
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── admin_controller.py
│   │   ├── owner_controller.py
│   │   ├── player_controller.py
│   │   └── webhook_controller.py
│   ├── middleware/             # Auth, RBAC, Tenant isolation, Rate limit
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   ├── rbac_middleware.py
│   │   └── tenant_middleware.py
│   ├── tasks/                  # Celery tasks
│   │   ├── __init__.py
│   │   ├── whatsapp_tasks.py
│   │   ├── payout_tasks.py
│   │   └── refund_tasks.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── redis_client.py
│   │   ├── s3_client.py
│   │   └── helpers.py
│   └── websocket/              # Socket.io event handlers
│       ├── __init__.py
│       └── events.py
├── migrations/                 # Alembic
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── celery_worker.py
├── wsgi.py                     # Gunicorn entry
├── requirements.txt
├── .env.example
└── Dockerfile
```

## Coding Patterns
### Flask
```python
# Controller pattern
from flask import Blueprint, request, g
from app.services import turf_service
from app.middleware import require_role, tenant_isolation

owner_bp = Blueprint('owner', __name__, url_prefix='/api/v1/owner')

@owner_bp.route('/turfs', methods=['POST'])
@require_role(['turf_owner'])
@tenant_isolation
def create_turf():
    data = TurfCreateSchema(**request.get_json())
    turf = turf_service.create_turf(g.current_user.id, data)
    return success_response(turf, 201)
```

### Service Pattern
```python
class BookingService:
    def __init__(self, db, redis, razorpay):
        self.db = db
        self.redis = redis
        self.razorpay = razorpay

    def create_booking(self, player_id: UUID, turf_sport_id: UUID, slot_ids: list[UUID]) -> Booking:
        # Validate slots are available (SELECT FOR UPDATE)
        # Calculate pricing
        # Create Razorpay order
        # Save booking as pending_payment
        # Return booking + order_id
```

### SQLAlchemy Model
```python
from sqlalchemy import String, ForeignKey, DateTime, Enum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
import uuid
from datetime import datetime

class Turf(Base):
    __tablename__ = 'turfs'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    amenities: Mapped[dict] = mapped_column(MySQLJSON, default=dict)
    operating_hours: Mapped[dict] = mapped_column(MySQLJSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
```

### React Component Pattern
```tsx
// No default exports. Named exports only.
// Props interface always exported.
// Use React.FC sparingly; prefer function declarations.

import { useState } from 'react';
import { Slot } from '@/types';

interface SlotCellProps {
  slot: Slot;
  isLocked: boolean;
  onSelect: (slotId: string) => void;
}

export function SlotCell({ slot, isLocked, onSelect }: SlotCellProps): JSX.Element {
  const statusColors = {
    available: 'bg-green-100 text-green-800',
    booked: 'bg-red-100 text-red-800',
    blocked: 'bg-gray-100 text-gray-800',
  };

  return (
    <button
      disabled={slot.status !== 'available' || isLocked}
      onClick={() => onSelect(slot.id)}
      className={`p-2 rounded ${statusColors[slot.status]} disabled:opacity-50`}
    >
      {slot.start_time} - {slot.end_time}
    </button>
  );
}
```

## Implementation Order
1. **Week 1**: Database models + Alembic migrations. Flask app factory. Config. Redis/S3 clients. Auth service + JWT middleware. Basic registration/login.
2. **Week 2**: Turf owner turf CRUD + S3 upload. Sport management. Slot generation engine (auto-create slots from operating_hours). Owner calendar read API.
3. **Week 3**: Player discovery API. Slot availability API. Socket.io setup. Redis lock implementation. React frontend scaffold + Tailwind. Player home + turf detail.
4. **Week 4**: Razorpay integration. Booking creation + payment flow. Webhook handler. Booking confirmation. React calendar grid + slot selection + Razorpay checkout.
5. **Week 5**: Cancellation + refund engine. WhatsApp service + Celery tasks. Notification templates. Owner slot blocker (API + UI). Socket.io real-time updates.
6. **Week 6**: RazorpayX payouts. Owner analytics. Admin dashboard (users, analytics, payouts). Player my-bookings + cancellation UI.
7. **Week 7**: E2E testing. Concurrency testing (Locust). Security hardening. Mobile responsiveness. Bug fixes.
8. **Week 8**: VPS deployment. Nginx config. SSL. Monitoring. Beta launch.

## Testing Requirements
- **Unit**: pytest. Mock external APIs (Razorpay, WhatsApp). Test refund calculation, slot blocking, pricing logic.
- **Integration**: Test database transactions. Test Redis locks. Test Socket.io events.
- **E2E**: Playwright. Player books a slot. Owner blocks a slot. Admin approves owner.
- **Load**: Locust. 50 concurrent users attempt to book the same slot. Verify only 1 succeeds; rest get conflict.

## Environment Variables
```bash
# App
FLASK_ENV=production
SECRET_KEY=32char_random
JWT_SECRET=32char_random
FRONTEND_URL=https://turfapp.in

# DB
DATABASE_URL=mysql+pymysql://user:pass@shared-mysql:3306/turf_saas

# Redis
REDIS_URL=redis://redis:6379/0

# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET=turf-saas-uploads
S3_REGION=ap-south-1

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
RAZORPAYX_KEY_ID=xxx
RAZORPAYX_KEY_SECRET=xxx

# WhatsApp
TWOFACTOR_API_KEY=xxx
GUPSHUP_API_KEY=xxx
GUPSHUP_APP_NAME=xxx

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

## Deployment Checklist
- [ ] Ubuntu 22.04 VPS with Nginx, MySQL 8, Redis 7, Python 3.12, Node 20.
- [ ] Nginx reverse proxy to Gunicorn (Unix socket). Static files from `frontend/dist`.
- [ ] SSL via Let's Encrypt (Certbot).
- [ ] Gunicorn: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker wsgi:app`.
- [ ] Celery: `celery -A celery_worker worker -l info -Q whatsapp,payouts,refunds`.
- [ ] Systemd services for app, celery, nginx, redis, mysql.
- [ ] Firewall: 80, 443, 22 only.
- [ ] S3 bucket: private, CORS configured for frontend domain.
- [ ] Razorpay webhooks: point to `https://api.turfapp.in/api/v1/webhooks/razorpay`.
- [ ] WhatsApp provider callbacks: point to `https://api.turfapp.in/api/v1/webhooks/whatsapp`.
