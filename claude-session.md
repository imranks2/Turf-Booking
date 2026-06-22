# CLAUDE SESSION — Turf SaaS Platform

## Session Protocol
- Read this file at the start of every session.
- Update the "Current Focus" and "Completed" sections before ending session.
- If a task is too large, break it into sub-tasks and update this file.
- Do not start a new module until the current module is marked complete.

## Project Status

### Completed
- [x] Week 1: Database models + migrations
- [x] Week 1: Flask app factory + config
- [x] Week 1: Redis/S3 clients
- [x] Week 1: Auth service + JWT middleware
- [x] Week 1: Registration/Login APIs
- [x] Week 2: Turf CRUD + S3 upload
- [x] Week 2: Sport management
- [x] Week 2: Slot generation engine
- [x] Week 2: Owner calendar read API
- [x] Week 3: Player discovery API
- [x] Week 3: Slot availability API
- [x] Week 3: Socket.io setup
- [x] Week 3: Redis lock implementation
- [x] Week 3: React scaffold + Tailwind
- [x] Week 3: Player home + turf detail
- [x] Week 4: Razorpay integration
- [x] Week 4: Booking creation + payment flow
- [x] Week 4: Webhook handler
- [x] Week 4: Booking confirmation
- [x] Week 4: React calendar grid + checkout
- [x] Week 5: Cancellation + refund engine
- [x] Week 5: WhatsApp service + Celery
- [x] Week 5: Owner slot blocker
- [x] Week 5: Socket.io real-time
- [x] Week 6: RazorpayX payouts
- [x] Week 6: Owner analytics
- [x] Week 6: Admin dashboard
- [x] Week 6: Player my-bookings
- [x] Week 7: E2E testing
- [x] Week 7: Concurrency testing
- [x] Week 7: Security hardening
- [x] Week 7: Mobile responsiveness
- [x] Week 8: VPS deployment (compose + systemd + scripts)
- [x] Week 8: Nginx + SSL (config + Certbot steps)
- [~] Week 8: Beta launch (artifacts ready; needs real infra + secrets)

### Current Focus
Module: Week 8 — Deployment artifacts + initial migration (COMPLETE). All 8 weeks done.
Task: docker-compose, Dockerfiles, nginx (host+container), systemd units, deploy.sh, README, Alembic 0001
Files: docker-compose.yml, nginx.conf, frontend/{Dockerfile,nginx.conf,.dockerignore}, backend/.dockerignore, systemd/*.service, scripts/deploy.sh, README.md, backend/migrations/versions/0001_initial.py
Blockers: NONE for code. Remaining are infra/runtime only — beta launch needs a real VPS, MySQL/Redis, and live Razorpay(X)/WhatsApp/AWS secrets. Initial migration bootstraps from SQLAlchemy metadata (verified upgrade+downgrade on sqlite); regenerate via autogenerate once on MySQL if a hand-authored diff is preferred.

### Next Up (post-MVP / optional)
1. Run Playwright E2E + Locust against the live stack; tune.
2. Add nightly slot-generation + 2h kickoff-reminder Celery beat schedules.
3. Add S3 image upload to owner TurfForm UI (server multipart path already exists).

## Session Notes
<!-- Add timestamped notes per session -->

### 2026-06-03
- Initial project setup. Created claude.md, claude-memory.md, claude-session.md.
- Week 1 implemented: backend package scaffold under `backend/app/` (config, extensions, exceptions, models, schemas/auth, services/auth_service, middleware, controllers/auth, websocket, tasks, utils). Alembic configured (`migrations/env.py` reads Base.metadata + settings.DATABASE_URL). requirements.txt, .env.example, Dockerfile, wsgi.py, celery_worker.py.
- Models: User, SaasAdminProfile, TurfOwnerProfile, Player, Turf, Sport, TurfSport, Slot, SlotBlock, Booking, Payment, DailyAnalytics, AuditLog, NotificationLog. All indexes per spec.
- Auth: bcrypt (cost 12), JWT access (15m, HS256, tenant_id for owners), SHA-256-hashed refresh tokens in Redis (7d), HTTP-only refresh cookie scoped to /api/v1/auth, password reset (1h Redis token). require_auth / require_role / tenant_isolation decorators.
- Unit tests: tests/unit/test_auth.py (password roundtrip, token claims, schema validation). All files pass py_compile.
- Week 2 implemented: `schemas/turf.py` (TurfCreate/Update, DayHours w/ HH:MM + close>open validation, TurfSportCreate/Update, CalendarQuery, GenerateSlots), `services/turf_service.py` (tenant-scoped turf CRUD + soft delete, get-or-create Sport + TurfSport, `build_day_slots`, `generate_slots` idempotent 14-day engine preserving existing slots, `get_calendar_slots`), `controllers/owner_controller.py` (turfs GET/POST[multipart S3 up to 10 imgs]/PUT/DELETE, turf sports GET/POST/PUT, slots GET calendar, slots/generate). owner_bp registered.
- Tests: tests/unit/test_slot.py (build_day_slots hourly/partial/custom, turf schema validation) + tests/integration/test_turf_flow.py (sqlite: turf create, sport add, slot gen count=5 over Mon/Tue, idempotent re-run=0, calendar read, tenant isolation NotFound). Full suite: 14 passed. MySQLJSON columns confirmed working under sqlite for tests.
- Note: added owner utility `POST /owner/slots/generate` (not in original spec) to trigger the generation engine on demand; nightly Celery beat job still pending (Week 5/scheduling).
- Week 3 backend: `services/player_service.py` (cross-tenant discovery w/ city/sport/price DB filters + Python amenity-subset, haversine radius sort, weekday-open filter, pagination; turf detail w/ sports + operating_hours; available-only slots; list_sports/list_cities), `controllers/player_controller.py` (public GET /turfs, /turfs/:id, /turfs/:id/slots, /sports, /cities — player_bp under /api/v1), `websocket/events.py` (join_turf_room, join_slot_room, lock_slot[Redis NX EX300 → slot_locked|booking_conflict], unlock_slot[owner-verify], block_slot[owner DB update + lock release]). Tests: tests/integration/test_player_flow.py (discovery by city/price, amenity filter, available excludes booked, detail/lookups). Full suite 18 passing.
- Week 3 frontend: Vite+React19+TS5.5(strict)+Tailwind3.4 scaffold. types/index.ts, services/{api(axios+refresh interceptor),socket,razorpay}, stores/appStore(zustand), contexts/{AuthContext,SocketContext}, hooks/{useAuth,useSocket,useTurfs(TanStack Query v5)}, utils/{constants,formatters(INR),validators(zod)}, components/ui/{Button,Input,Card,Badge,Spinner}, components/turf/{TurfCard,AmenityTag}, components/layout/TopNav, pages/player/{Home(discovery+filters),TurfDetail(sports/hours/slots)}, App.tsx(router+QueryClient+AuthProvider), main.tsx. Verified: `npm run typecheck` + `npm run build` both pass (152 modules).
- Frontend gotcha: React 19 @types/react removed the global `JSX` namespace; added `src/global.d.ts` shim aliasing `JSX.*` → `React.JSX.*` so the CLAUDE.md `: JSX.Element` style compiles. tsconfig project-references dropped (single `tsc --noEmit` typecheck; Vite bundles).
- Week 4 backend: `services/payment_service.py` (pure `compute_pricing` [Decimal, ROUND_HALF_UP; total=price×hrs, advance=total×pct, convenience=₹20×hrs, platform=₹40×hrs, owner_payout=total−₹20×hrs, order_paise=(advance+convenience)×100] and `compute_refund` [≥24h=100%, ≥12h=50%, else 0%, convenience never refunded] + `hours_until`). `razorpay_service.py` (lazy client, create_order/create_refund, verify_payment_signature, HMAC-SHA256 verify_webhook_signature). `booking_service.py` (create_booking: SELECT FOR UPDATE slots, Redis lock acquire/verify per player, pricing, unique 8-char code, Razorpay order, advance Payment row; confirm_booking: idempotent → slots booked + lock release + payout Payment row pending; fail_booking; list/get player bookings). `controllers/webhook_controller.py` (POST /webhooks/razorpay: HMAC verify + Redis dedupe via X-Razorpay-Event-Id|payment.id, dispatch payment.captured/failed/refund.processed/payout.*; POST /webhooks/whatsapp ack). Booking routes added to player_controller (POST/GET /bookings, GET /bookings/:id, require_auth).
- Week 4 design note: booking confirmation is webhook-driven. POST /bookings returns {booking_id, razorpay_order_id, amount}; frontend opens Razorpay checkout; on success/dismiss it navigates to /bookings/:id which **polls GET /bookings/:id every 2s until status=confirmed|cancelled** (slots only flip to `booked` on the `payment.captured` webhook → confirm_booking). No client-side trust of payment result.
- Week 4 tests: tests/unit/test_booking.py (pricing 2hr/1hr, refund 100/50/0 + boundaries inclusive, hours_until) + tests/integration/test_booking_flow.py (create→confirm: slots booked + payout row ₹1960 pending; confirm idempotent = 1 payout; double-booking after confirm → Conflict; Redis + razorpay.create_order monkeypatched). Full suite: 28 passing.
- Week 4 frontend: components/calendar/{SlotCell(selectable, status colors, lock icon),CalendarGrid}, components/booking/{PriceBreakdown(client preview),BookingFlow(create booking→openCheckout→navigate),BookingCard}, hooks/useBookings(useCreateBooking mutation, useMyBookings, useBooking w/ poll-until-confirmed), pages/player/{BookingConfirm(polls),MyBookings}, pages/Login(login+player register toggle, not in original structure but needed). TurfDetail rewritten for multi-slot select + hours calc + BookingFlow. App wraps SocketProvider; routes /login,/bookings,/bookings/:id added. typecheck+build pass (204 modules).
- Week 5 backend: `services/whatsapp_service.py` (7 Jinja2 templates per spec; `render_template`; `send_template` logs NotificationLog + dispatches Gupshup/2Factor, status='skipped' when unconfigured). `booking_service.cancel_booking` (refund via compute_refund on hours-to-kickoff from earliest slot, slots→available + booking_id cleared, refund Payment row pending, refund_status pending|not_applicable; blocks re-cancel of cancelled/completed/no_show) + `mark_no_show`. `turf_service` slot blocker: `block_slots` (range, rejects booked, SlotBlock audit row, socket `slot_blocked` emit), `unblock_slot` (→available, `slot_available` emit), `bulk_block_slots` (weekday filter over date range). Celery `tasks/{whatsapp_tasks(send_template+notify_booking_confirmed),refund_tasks(process_refund: razorpay refund + retry 5m/30m/2h + refund_processed WA),payout_tasks(process_payout: RazorpayX IMPS, kyc_verified gate, retry)}`. Routes: owner /slots/block,/unblock,/bulk-block,/bookings/:id/no-show; player /bookings/:id/cancel. webhook payment.captured now enqueues notify_booking_confirmed + process_payout (best-effort, lazy import).
- Week 5 tests: tests/unit/test_whatsapp.py (render confirmed/unknown), tests/integration/test_cancel_flow.py (full refund >24h=₹500 + slots freed + refund row; 0% <12h; no double-cancel), tests/integration/test_slot_block.py (block range=2, unblock, bulk-block weekday=4). Full suite: 36 passing. Socket emits wrapped in try/except (no live server in tests).
- Week 5 deferred: nightly slot-generation Celery beat + 2h kickoff reminder beat NOT added (would need task files beyond the 3 listed in structure; on-demand POST /owner/slots/generate covers generation for now).
- Week 6 backend: `services/analytics_service.py` (owner_analytics [totals + by_sport + daily time_series, tenant-scoped, confirmed+completed], admin_analytics [+ active_owners/players], list_users [q/role/status + paginate + profile name], set_user_active, list_payouts [tenant-optional], list_audit_logs, record_audit). `payment_service.setup_payout_account` (RazorpayX Contact+FundAccount → kyc_status=verified). `razorpay_service` create_contact/create_fund_account (RazorpayX REST). `booking_service.list_owner_bookings` (turf_id/status filter). `admin_controller.py` (GET /users, PATCH approve/suspend [+audit], GET /analytics, GET /payouts, POST /payouts/:id/retry→process_payout, GET /audit-logs). owner_controller +GET /bookings,/analytics,/payouts, PUT /profile/bank. admin_bp registered. Schemas: payment.py +BankDetails(IFSC regex)/AnalyticsQuery/Pagination.
- Week 6 tests: tests/integration/test_analytics_admin.py (owner totals rev=₹1000/payout=₹980/by_sport, admin totals + active counts, suspend/reactivate, owner payout listing tenant-scoped). Full suite: 40 passing.
- Week 6 frontend: hooks useOwnerTurfs (turfs/create/analytics/bookings/payouts/slots/block/generate), useAdmin (users/setStatus/analytics/payouts/retry), useBookings +useCancelBooking. components analytics/{KpiCard,RevenueChart(recharts)}, ui/Table, layout/{Sidebar,RequireRole role-guard}. pages owner/{Dashboard,Turfs,TurfForm,Calendar(slot gen+block),Bookings,Analytics}, admin/{Dashboard,Users(approve/suspend),Payouts(retry),Analytics}. Player cancel UI on BookingConfirm. App role-guarded routes /owner/* /admin/*; TopNav role link. typecheck+build pass (1019 modules; recharts → ~828kB bundle, chunk-size warning only). NOTE: TurfForm posts JSON (no S3 image upload in form yet — multipart create exists server-side).
- Week 7 security: `middleware/rate_limit_middleware.py` (before_request on /api/*: IP 100/min + per-user 20/min via Redis INCR+EXPIRE windows, decodes bearer for user key, **fail-open** if Redis down). app factory adds security headers (X-Content-Type-Options, X-Frame-Options DENY, Referrer-Policy, CSP default-src 'self', Permissions-Policy; HSTS in prod) via after_request + `init_rate_limiting`. Verified: rate-limit returns 429 after limit, /health exempt, headers present, fail-open works without Redis.
- Week 7 tests authored: backend/tests/load/locustfile.py (50 users book same slot → counts confirmed vs 409 conflicts; needs LOAD_TURF_SPORT_ID/LOAD_SLOT_ID env + running stack). frontend/e2e/{player_booking,owner_block,admin_approve}.spec.ts + playwright.config.ts (chromium + Pixel5 mobile; baseURL E2E_BASE_URL); `npm run test:e2e`. These require a running app — NOT executed here. backend/tests/integration/test_rate_limit.py runs locally (fake counter): 429 after 3, /health exempt.
- Week 7 mobile: `components/layout/MobileNav.tsx` (horizontal scroll nav, md:hidden) added to RequireRole so owner/admin nav is reachable on mobile (Sidebar is md:block only). Player grids already responsive. Full backend suite: 42 passing; frontend typecheck passes.
- Week 8 deployment: `migrations/versions/0001_initial.py` (bootstraps schema via Base.metadata.create_all; verified `alembic upgrade head` + `downgrade base` on sqlite). `docker-compose.yml` (mysql8+redis7 healthchecks, backend [alembic upgrade head→gunicorn geventwebsocket worker], celery worker, flower, frontend nginx image; `docker compose config` validates). `frontend/Dockerfile` (multi-stage node20 build→nginx1.27) + `frontend/nginx.conf` (SPA + proxy /api + /socket.io ws upgrade). `nginx.conf` (host: 80→443 redirect, TLS, unix-socket upstream, SPA, ws, security headers, Certbot acme path). `systemd/{turf-backend(ExecStartPre alembic upgrade, gunicorn unix socket),turf-celery}.service`. `scripts/deploy.sh`. `README.md`. `.dockerignore` x2.
- Week 8 note: Gunicorn uses **GeventWebSocketWorker** (Flask-SocketIO is WSGI) — the spec checklist's `uvicorn.workers.UvicornWorker` is ASGI-only and would not serve this app; documented in README. backend/.env created from example for local docker (gitignored, placeholder values).
- Post-Week-8 fix: Docker flower/backend crashed with `ModuleNotFoundError: No module named 'pkg_resources'`. Root cause: `razorpay==1.4.2` hard-imports pkg_resources, which `setuptools>=82.0.1` (intentional pin) no longer ships (removed in setuptools 81). Resolution (user choice): bumped `razorpay==1.4.2 → 2.0.1` (guards the pkg_resources import) and kept setuptools>=82. Verified: setuptools 82 + razorpay 2.0.1 → `import razorpay` + `create_app()` OK with pkg_resources absent; SDK methods order.create/payment.refund/utility.verify_payment_signature present; RazorpayX uses raw requests (unaffected); 42 tests still pass. Updated claude.md tech-stack to Razorpay 2.0.1. NOTE: compose db/redis are commented out + `shared-net` external network (user runs shared MySQL/Redis); DATABASE_URL host is `shared-mysql`.
- Dependency refresh (user-requested "latest & working"): upgraded ALL packages to current latest and re-pinned. Backend (requirements.txt): Flask 3.1.3, Flask-SocketIO 5.6.1, Flask-CORS 6.0.5, gunicorn 26.0.0, uvicorn 0.49.0, gevent 26.5.0, SQLAlchemy 2.0.51, alembic 1.18.4, PyMySQL 1.2.0, PyJWT 2.13.0, bcrypt 5.0.0, python-jose 3.5.0, redis 8.0.0, celery 5.6.3, razorpay 2.0.1, boto3 1.43.34, pydantic 2.13.4, pydantic-settings 2.14.2, python-socketio 5.16.3, pytest 9.1.1 (+ setuptools>=82.0.1 kept). Frontend (package.json): react 19.2, TypeScript **6.0**, Vite **8**, @vitejs/plugin-react 6, zustand 5, @tanstack/react-query 5.101, axios 1.18, socket.io-client 4.8, @playwright/test 1.61. Held at current major to avoid breaking migrations: tailwindcss 3.4.19, recharts 2.15, react-router-dom 6.30, zod 3.25.
- Upgrade fixes: TS 6 deprecates `baseUrl` (errors) → removed `baseUrl` from frontend/tsconfig.json (paths resolve relative to tsconfig). Vite 8 needs Node ≥20.19/22.12 → bumped frontend/Dockerfile base `node:20-alpine`→`node:22-alpine`. Verified: backend **42 tests pass**, alembic upgrade/downgrade OK on 1.18.4, app constructs; frontend **typecheck + build pass** (Vite 8, TS 6). Note major bumps that passed cleanly with no code changes: Flask-CORS 4→6, bcrypt 4→5, redis 4→8, pytest 8→9, celery 5.3→5.6.
- Demo seed: `backend/seed.py` (run `python seed.py` or `docker compose exec backend python seed.py`). Idempotent (upserts by email / fixed booking_code DEMOBOOK / create_all). Seeds admin@turfapp.in (Admin@12345), owner1/owner2@turfapp.in (Owner@12345, KYC verified + active subscription + dummy razorpay ids), player@turfapp.in (Player@12345); 2 turfs (Pune/Mumbai, 7-day 06:00–23:00 hours), 4 turf-sports, 14 days of slots (952 rows), 1 confirmed booking with advance+payout Payment rows so owner/admin analytics show data. Verified: 2 runs → 4 users/2 turfs/4 turf_sports/952 slots/1 booking/2 payments, no dupes. Uses auth_service/turf_service/payment_service; no Redis/Razorpay needed.
- Bugfixes (demo run): (1) `GET /owner/turfs` crashed frontend (`turf.sports.length` undefined) — owner controller serialized via `model_to_dict` (raw columns, no sports). Added `turf_service.serialize_turf(db, turf)` (columns + active sports view + min_price_per_hour) and used it in owner `_turf_out`. (2) **Rate-limit 429 storm** — `_incr_window` reset EXPIRE on every call so the window never expired under continuous use (counter climbed forever → permanent 429). Fixed to set TTL only when count==1 (true fixed window). Also raised defaults RATE_LIMIT_IP_PER_MINUTE 100→1000, USER 20→300 (20/min was unusable for an authed SPA dashboard firing ~6-10 req/page). (3) Quieted benign `geventwebsocket` DEBUG "Failed to write closing frame" by setting that logger to WARNING. Verified: 43 tests pass; HTTP smoke of GET /owner/turfs (auth) returns sports+min_price, status 200.
- UI redesign (design-mirror, turfbooking.in-inspired): sporty turf-green theme. tailwind.config.js (brand green 50-950 + lime accent, Poppins headings/Inter body, soft/card shadows, hero-overlay + brand-gradient bg images, fade-in/slide-up anims). index.css (@import Google Fonts, font-heading on h1-4). NEW: utils/images.ts (royalty-free Unsplash hero/sport/turf URLs — all 10 IDs GET-verified 200, onError→gradient fallback), components/turf/HeroSlider.tsx (auto-advancing 3-slide hero w/ search-panel children + dots), components/layout/Footer.tsx. Restyled: ui/Button (pill rounded-full), layout/TopNav (glassy sticky brand + ⚽ logo), turf/TurfCard (image w/ price chip + hover lift). pages/player/Home rebuilt (hero slider + city/sport search + sport-category grid + 3-step how-it-works + results w/ price filter + footer); TurfDetail (image fallback + footer). Owner/admin dashboards inherit theme globally. Verified typecheck+build pass. NOTE: design-mirror's Bright Data capture skipped (no BRIGHTDATA_API_KEY/ZONE) — used WebFetch on turfbooking.in for design language instead.
- PROJECT STATUS: All 8 implementation weeks complete. Backend 42 tests green; frontend typecheck+build green; compose validates; migration up/down verified. Outstanding = live-infra only (real DB/Redis/Razorpay/WhatsApp/S3 secrets + VPS) and running E2E/Locust against a live stack.

## File Inventory

### Backend (Python/Flask)
| File | Status | Notes |
|------|--------|-------|
| app/__init__.py | CREATED | App factory |
| app/config.py | CREATED | Pydantic settings |
| app/extensions.py | CREATED | DB, Redis, S3, SocketIO |
| app/models/user.py | CREATED | User, AdminProfile, OwnerProfile, Player |
| app/models/turf.py | CREATED | Turf |
| app/models/sport.py | CREATED | Sport, TurfSport |
| app/models/slot.py | CREATED | Slot, SlotBlock |
| app/models/booking.py | CREATED | Booking, Payment |
| app/models/analytics.py | CREATED | DailyAnalytics, AuditLog, NotificationLog |
| app/schemas/auth.py | CREATED | Auth Pydantic schemas |
| app/schemas/turf.py | CREATED | Turf/sport/slot schemas |
| app/services/auth_service.py | CREATED | JWT, bcrypt, registration |
| app/services/turf_service.py | CREATED | Turf CRUD, sport mgmt, slot gen |
| app/controllers/owner_controller.py | CREATED | Owner turf/sport/slot endpoints |
| app/services/player_service.py | CREATED | Discovery, slots, sports/cities |
| app/controllers/player_controller.py | CREATED | Public discovery + slot endpoints |
| app/websocket/events.py | CREATED | Socket.io rooms + Redis slot locks |
| app/services/booking_service.py | CREATED | Booking create/confirm/cancel, locking |
| app/services/payment_service.py | CREATED | Pricing + refund calc (pure) |
| app/services/razorpay_service.py | CREATED | Razorpay orders/refunds/signatures |
| app/services/whatsapp_service.py | CREATED | Jinja2 templates + provider send |
| app/controllers/webhook_controller.py | CREATED | Razorpay + WhatsApp webhooks |
| app/schemas/booking.py, payment.py | CREATED | Booking/payment schemas |
| app/tasks/whatsapp_tasks.py | CREATED | send_template, notify_booking_confirmed |
| app/tasks/refund_tasks.py | CREATED | process_refund + retry |
| app/tasks/payout_tasks.py | CREATED | process_payout (RazorpayX) + retry |
| app/services/analytics_service.py | CREATED | Owner/admin analytics, users, payouts, audit |
| app/controllers/admin_controller.py | CREATED | Admin users/analytics/payouts/audit |
| app/services/whatsapp_service.py | NOT_CREATED | Template sends |
| app/controllers/auth_controller.py | CREATED | Auth blueprint (others pending) |
| app/middleware/ | CREATED | Auth, RBAC, tenant (rate limit pending) |
| app/tasks/__init__.py | CREATED | Celery app (task modules pending) |
| app/websocket/events.py | CREATED | Socket.io connect/disconnect stub |
| wsgi.py | CREATED | Gunicorn entry |
| celery_worker.py | CREATED | Celery app |
| requirements.txt | CREATED | All dependencies |
| .env.example | CREATED | Template env file |
| Dockerfile | CREATED | Python 3.12 slim + gunicorn |
| migrations/env.py | CREATED | Alembic env (autogenerate ready) |

### Frontend (React/TypeScript)
| File | Status | Notes |
|------|--------|-------|
| src/main.tsx | NOT_CREATED | Entry point |
| src/App.tsx | NOT_CREATED | Router + guards |
| src/components/ui/ | NOT_CREATED | Base UI components |
| src/components/layout/ | NOT_CREATED | Sidebar, nav |
| src/components/calendar/ | NOT_CREATED | Calendar grid, slot cell |
| src/components/booking/ | NOT_CREATED | Booking flow, price breakdown |
| src/components/turf/ | NOT_CREATED | Turf card, detail |
| src/components/analytics/ | NOT_CREATED | Charts, KPIs |
| src/hooks/ | NOT_CREATED | Custom hooks |
| src/contexts/ | NOT_CREATED | Auth, Socket |
| src/services/api.ts | NOT_CREATED | Axios instance |
| src/services/razorpay.ts | NOT_CREATED | Checkout integration |
| src/services/socket.ts | NOT_CREATED | Socket.io client |
| src/stores/appStore.ts | NOT_CREATED | Zustand store |
| src/types/index.ts | NOT_CREATED | All TS interfaces |
| src/utils/ | NOT_CREATED | Constants, formatters, validators |
| src/pages/admin/ | NOT_CREATED | Admin routes |
| src/pages/owner/ | NOT_CREATED | Owner routes |
| src/pages/player/ | NOT_CREATED | Player routes |
| vite.config.ts | NOT_CREATED | Vite config |
| tailwind.config.js | NOT_CREATED | Tailwind config |
| tsconfig.json | NOT_CREATED | TS strict config |
| package.json | NOT_CREATED | Dependencies |

### Infrastructure
| File | Status | Notes |
|------|--------|-------|
| backend/Dockerfile | CREATED | Python 3.12 + gunicorn |
| frontend/Dockerfile | CREATED | Multi-stage node→nginx |
| docker-compose.yml | CREATED | Full stack (validated) |
| nginx.conf | CREATED | Host reverse proxy + SSL |
| frontend/nginx.conf | CREATED | Container SPA + proxy |
| systemd/*.service | CREATED | turf-backend, turf-celery |
| scripts/deploy.sh | CREATED | Deployment script |
| README.md | CREATED | Setup + deploy docs |
| migrations/versions/0001_initial.py | CREATED | Initial schema (up/down verified) |

## Testing Inventory
| Test | Status | Notes |
|------|--------|-------|
| tests/unit/test_auth.py | CREATED | Password, JWT, schema (6) |
| tests/unit/test_booking.py | CREATED | Pricing, refund calc (7) |
| tests/unit/test_slot.py | CREATED | Slot gen + turf schema (6) |
| tests/integration/test_turf_flow.py | CREATED | Turf CRUD + slot gen |
| tests/integration/test_player_flow.py | CREATED | Discovery + availability |
| tests/integration/test_booking_flow.py | CREATED | Booking create/confirm |
| tests/integration/test_api.py | NOT_CREATED | HTTP-level flow tests |
| tests/integration/test_socket.py | NOT_CREATED | Socket.io tests |
| frontend/e2e/*.spec.ts | CREATED | Playwright (player/owner/admin) |
| backend/tests/load/locustfile.py | CREATED | Slot contention load test |
| backend/tests/integration/test_rate_limit.py | CREATED | Rate-limit 429 + exempt |
| backend/tests/integration/test_analytics_admin.py | CREATED | Analytics + admin mgmt |

## Environment Setup Checklist
- [ ] MySQL 8 running locally
- [ ] Redis 7 running locally
- [ ] Python 3.12 venv created
- [ ] Node 20 installed
- [ ] AWS S3 bucket created (dev)
- [ ] Razorpay test account
- [ ] 2Factor/Gupshup test account
- [ ] `.env` file configured
