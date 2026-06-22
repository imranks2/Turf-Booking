from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from sqlalchemy import select

from app.extensions import Base, db_session, engine
from app.models.booking import Payment, PaymentType
from app.models.user import Player, User, UserRole
from app.schemas.turf import TurfCreateSchema, TurfSportCreateSchema
from app.services import analytics_service, auth_service, booking_service, turf_service


@pytest.fixture
def db(monkeypatch):
    Base.metadata.create_all(engine)
    monkeypatch.setattr(booking_service.rc, "get_slot_lock_owner", lambda _s: None)
    monkeypatch.setattr(booking_service.rc, "acquire_slot_lock", lambda _s, _p: True)
    monkeypatch.setattr(booking_service.rc, "release_slot_lock", lambda _s: None)
    monkeypatch.setattr(
        booking_service.razorpay_service,
        "create_order",
        lambda amount_paise, receipt, notes=None: {"id": "order_a", "amount": amount_paise},
    )
    yield db_session
    db_session.remove()
    Base.metadata.drop_all(engine)


def _seed_confirmed(db) -> dict:
    owner = User(email="o@t.in", phone="+919812345611", password_hash=auth_service.hash_password("password123"), role=UserRole.turf_owner, is_active=True)
    puser = User(email="p@t.in", phone="+919812345612", password_hash=auth_service.hash_password("password123"), role=UserRole.player, is_active=True)
    db.add_all([owner, puser])
    db.commit()
    db.add(Player(user_id=puser.id, name="Sam", phone="+919812345612"))
    db.commit()
    turf = turf_service.create_turf(db, owner.id, TurfCreateSchema(name="Arena", address="MG Road", city="Pune", operating_hours={"mon": {"open": "06:00", "close": "09:00"}}), [])
    ts = turf_service.add_turf_sport(db, owner.id, turf.id, TurfSportCreateSchema(sport_name="Football", price_per_hour=1000))
    turf_service.generate_slots(db, owner.id, ts.id, days=1, start_date=date(2026, 6, 8))
    from app.models.slot import Slot

    slot = db.scalars(select(Slot).where(Slot.turf_sport_id == ts.id)).first()
    booking_service.create_booking(db, puser.id, ts.id, [slot.id])
    booking_service.confirm_booking(db, "order_a", "pay_a")
    return {"owner": owner, "puser": puser}


def test_owner_analytics_totals(db):
    seed = _seed_confirmed(db)
    result = analytics_service.owner_analytics(db, seed["owner"].id, None, None)
    assert result["total_bookings"] == 1
    assert result["total_revenue"] == 1000.0
    assert result["total_owner_payouts"] == 980.0
    assert result["by_sport"][0]["sport"] == "Football"
    assert len(result["time_series"]) == 1


def test_admin_analytics_and_users(db):
    _seed_confirmed(db)
    admin_view = analytics_service.admin_analytics(db, None, None)
    assert admin_view["total_bookings"] == 1
    assert admin_view["active_owners"] == 1
    assert admin_view["active_players"] == 1

    users = analytics_service.list_users(db, q=None, role="turf_owner", status="active", page=1, limit=10)
    assert users["total"] == 1
    assert users["items"][0]["name"] == "Arena" or users["items"][0]["role"] == "turf_owner"


def test_admin_suspend_and_reactivate(db):
    seed = _seed_confirmed(db)
    suspended = analytics_service.set_user_active(db, seed["owner"].id, False)
    assert suspended.is_active is False
    active = analytics_service.set_user_active(db, seed["owner"].id, True)
    assert active.is_active is True


def test_owner_payout_listing(db):
    seed = _seed_confirmed(db)
    payouts = analytics_service.list_payouts(db, None, 1, 20, tenant_id=seed["owner"].id)
    assert payouts["total"] == 1
    assert payouts["items"][0]["amount"] == 980.0

    payout = db.scalar(select(Payment).where(Payment.type == PaymentType.payout))
    assert payout.tenant_id == seed["owner"].id
