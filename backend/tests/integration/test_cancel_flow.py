from __future__ import annotations

import os
from datetime import date, datetime, timezone

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from sqlalchemy import select

from app.extensions import Base, db_session, engine
from app.models.booking import BookingStatus, Payment, PaymentType
from app.models.slot import Slot, SlotStatus
from app.models.user import Player, User, UserRole
from app.schemas.turf import TurfCreateSchema, TurfSportCreateSchema
from app.services import auth_service, booking_service, turf_service


@pytest.fixture
def db(monkeypatch):
    Base.metadata.create_all(engine)
    monkeypatch.setattr(booking_service.rc, "get_slot_lock_owner", lambda _s: None)
    monkeypatch.setattr(booking_service.rc, "acquire_slot_lock", lambda _s, _p: True)
    monkeypatch.setattr(booking_service.rc, "release_slot_lock", lambda _s: None)
    monkeypatch.setattr(
        booking_service.razorpay_service,
        "create_order",
        lambda amount_paise, receipt, notes=None: {"id": "order_x", "amount": amount_paise},
    )
    yield db_session
    db_session.remove()
    Base.metadata.drop_all(engine)


def _booked(db) -> dict:
    owner = User(email="o@t.in", phone="+919812345601", password_hash=auth_service.hash_password("password123"), role=UserRole.turf_owner, is_active=True)
    puser = User(email="p@t.in", phone="+919812345602", password_hash=auth_service.hash_password("password123"), role=UserRole.player, is_active=True)
    db.add_all([owner, puser])
    db.commit()
    db.add(Player(user_id=puser.id, name="Sam", phone="+919812345602"))
    db.commit()
    turf = turf_service.create_turf(db, owner.id, TurfCreateSchema(name="Arena", address="MG Road", city="Pune", operating_hours={"mon": {"open": "06:00", "close": "09:00"}}), [])
    ts = turf_service.add_turf_sport(db, owner.id, turf.id, TurfSportCreateSchema(sport_name="Football", price_per_hour=1000))
    turf_service.generate_slots(db, owner.id, ts.id, days=1, start_date=date(2026, 6, 8))
    slot = db.scalars(select(Slot).where(Slot.turf_sport_id == ts.id)).first()
    booking_service.create_booking(db, puser.id, ts.id, [slot.id])
    booking_service.confirm_booking(db, "order_x", "pay_x")
    return {"puser": puser, "ts": ts, "slot_id": slot.id}


def test_cancel_full_refund_above_24h(db):
    seed = _booked(db)
    result = booking_service.cancel_booking(
        db, seed["puser"].id, _booking_id(db), reason="changed plans", now=datetime(2026, 6, 1, tzinfo=timezone.utc)
    )
    assert result["refund_percentage"] == 100
    assert float(result["refund_amount"]) == 500.0
    assert result["refund_status"] == "pending"

    slot = db.get(Slot, seed["slot_id"])
    assert slot.status == SlotStatus.available
    assert slot.booking_id is None

    refund_payment = db.scalar(select(Payment).where(Payment.type == PaymentType.refund))
    assert refund_payment is not None


def test_cancel_no_refund_under_12h(db):
    seed = _booked(db)
    result = booking_service.cancel_booking(
        db, seed["puser"].id, _booking_id(db), reason=None, now=datetime(2026, 6, 8, 0, 0, tzinfo=timezone.utc)
    )
    assert result["refund_percentage"] == 0
    assert float(result["refund_amount"]) == 0.0
    assert result["refund_status"] == "not_applicable"


def test_cannot_cancel_twice(db):
    seed = _booked(db)
    bid = _booking_id(db)
    booking_service.cancel_booking(db, seed["puser"].id, bid, reason=None, now=datetime(2026, 6, 1, tzinfo=timezone.utc))
    from app.exceptions import ValidationFailed

    with pytest.raises(ValidationFailed):
        booking_service.cancel_booking(db, seed["puser"].id, bid, reason=None, now=datetime(2026, 6, 1, tzinfo=timezone.utc))


def _booking_id(db) -> str:
    from app.models.booking import Booking

    return db.scalars(select(Booking).where(Booking.status == BookingStatus.confirmed)).first().id
