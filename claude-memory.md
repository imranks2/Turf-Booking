# CLAUDE MEMORY — Turf SaaS Platform

## Business Rules (Immutable)
- Platform fee: ₹40 per booked hour. Split: ₹20 from player (convenience fee), ₹20 from turf owner (service fee).
- Refund policy (hardcoded):
  - Cancel >24h before kickoff: 100% advance deposit refund.
  - Cancel 12-24h before: 50% advance deposit refund.
  - Cancel <12h before: 0% advance deposit refund.
  - Platform fee (₹20/hr) is NEVER refunded in any scenario.
- Slot lock duration: 5 minutes (300s Redis TTL).
- Owner payout = (slot_price × hours) - (₹20 × hours).
- Advance deposit percentage: Configurable per turf-sport (default 50%).
- Razorpay order amount = (advance_deposit) + (convenience_fee) in paise.
- Currency: INR only. All prices stored as Decimal (not float).

## Domain Entities
- **User**: Base entity. Role determines access. Email + phone unique.
- **Turf Owner**: Must complete KYC (bank details) before receiving payouts. RazorpayX Contact + Fund Account required.
- **Turf**: Physical venue. Has operating_hours JSON: `{mon: {open: "06:00", close: "23:00"}, ...}`.
- **Sport**: Global per tenant. e.g., "Cricket", "Football", "Badminton".
- **TurfSport**: Junction. Price per hour, deposit %, player limits. A turf can have multiple sports.
- **Slot**: 1-hour granularity (default). Auto-generated from operating_hours. Status: available, booked, blocked, maintenance.
- **Booking**: Links player + slots. booking_code = 8-char alphanumeric (URL-safe).
- **Payment**: Records Razorpay transactions. Types: advance, full, refund, payout.

## Multi-Tenancy Rules
- Every tenant-scoped query MUST include `tenant_id = current_user.id`.
- SaaS Admin queries have NO tenant filter.
- Player queries are cross-tenant (discovery) but bookings are filtered by `player_id`.
- `tenant_id` is injected via middleware from JWT payload.
- Soft deletes only (`is_active = false`). Never hard delete tenant data.

## KYC Flow
1. Owner registers → `is_active=false`, `kyc_status=pending`.
2. Admin approves → `is_active=true`, `kyc_status=pending` (bank not yet verified).
3. Owner adds bank details → system creates RazorpayX Contact + Fund Account → `kyc_status=verified`.
4. Payouts only processed if `kyc_status=verified`.

## Notification Triggers
| Event | Recipient | Template | Async |
|-------|-----------|----------|-------|
| Booking confirmed | Player | turf_booking_confirmed | Celery |
| 2h before kickoff | Player | turf_kickoff_reminder | Celery (scheduled) |
| Payment failed | Player | turf_payment_failed | Celery |
| Booking cancelled | Player | turf_booking_cancelled | Celery |
| Refund processed | Player | turf_refund_processed | Celery |
| New booking | Owner | turf_owner_new_booking | Celery |
| Payout initiated | Owner | turf_owner_payout | Celery |

## Redis Key Patterns
- `refresh_token:{hash}` → user_id (TTL: 7 days)
- `password_reset:{token}` → user_id (TTL: 1 hour)
- `slot_lock:{slot_id}` → player_id (TTL: 300s)
- `processed:{razorpay_payment_id}` → "1" (TTL: 24h) — webhook idempotency
- `rate_limit:{ip}` → count (TTL: 60s)
- `rate_limit:{user_id}` → count (TTL: 60s)
- `socket_room:{user_id}` → socket_id mapping

## S3 Structure
- `turfs/{turf_id}/{uuid}.jpg` — Turf images
- `players/{player_id}/{uuid}.jpg` — Profile images
- Pre-signed URLs: 1 hour expiry. Images served via CloudFront (optional).

## RazorpayX Payout States
1. On booking confirmation, create `Payment` row type=payout, status=pending.
2. Celery task calls RazorpayX Payouts API.
3. On `payout.processed` webhook → update status=processed.
4. On `payout.failed` webhook → update status=failed, queue retry (max 3).
5. Retry delays: 5min, 30min, 2hours.

## Calendar Generation
- Slots generated nightly (Celery beat) for next 14 days.
- If operating_hours change, regenerate future slots (preserve booked/blocked).
- Slot duration: 60 minutes (default). Start times align with operating_hours open time.
- Example: open=06:00, close=23:00 → slots: 06:00-07:00, 07:00-08:00, ..., 22:00-23:00.

## Security Checklist
- JWT secret rotated every 90 days (manual).
- Refresh tokens hashed with SHA-256 before Redis storage.
- Passwords: bcrypt cost factor 12.
- S3: bucket policy denies all, pre-signed URLs only.
- Rate limits: 100 req/min IP, 20 req/min user.
- SQL injection: ORM only. No f-strings in queries.
- XSS: CSP header, no innerHTML, sanitize inputs.
- Secrets: `.env` only, never in git.
