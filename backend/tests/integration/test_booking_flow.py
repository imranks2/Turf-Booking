from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest

from app.extensions import Base, db_session, engine
from app.models.booking import BookingStatus, Payment, PaymentStatus, PaymentType
from app.models.slot import Slot, SlotStatus
from app.models.user import Player, User, UserRole
from app.schemas.turf import TurfCreateSchema, TurfSportCreateSchema
from app.services import auth_service, booking_service, turf_service
from sqlalchemy import select


@pytest.fixture
def db(monkeypatch):
    Base.metadata.create_all(engine)
    monkeypatch.setattr(booking_service.rc, "get_slot_lock_owner", lambda _slot_id: None)
    monkeypatch.setattr(booking_service.rc, "acquire_slot_lock", lambda _slot_id, _player: True)
    monkeypatch.setattr(booking_service.rc, "release_slot_lock", lambda _slot_id: None)
    monkeypatch.setattr(
        booking_service.razorpay_service,
        "create_order",
        lambda amount_paise, receipt, notes=None: {"id": "order_test_123", "amount": amount_paise},
    )
    yield db_session
    db_session.remove()
    Base.metadata.drop_all(engine)


def _seed(db) -> dict:
    owner = User(
        email="o@t.in",
        phone="+919812345671",
        password_hash=auth_service.hash_password("password123"),
        role=UserRole.turf_owner,
        is_active=True,
    )
    player_user = User(
        email="p@t.in",
        phone="+919812345672",
        password_hash=auth_service.hash_password("password123"),
        role=UserRole.player,
        is_active=True,
    )
    db.add_all([owner, player_user])
    db.commit()
    player = Player(user_id=player_user.id, name="Pixel", phone="+919812345672")
    db.add(player)
    db.commit()

    turf = turf_service.create_turf(
        db,
        owner.id,
        TurfCreateSchema(
            name="Arena",
            address="MG Road",
            city="Pune",
            operating_hours={"mon": {"open": "06:00", "close": "09:00"}},
        ),
        [],
    )
    ts = turf_service.add_turf_sport(
        db, owner.id, turf.id, TurfSportCreateSchema(sport_name="Football", price_per_hour=1000)
    )
    turf_service.generate_slots(db, owner.id, ts.id, days=1, start_date=date(2026, 6, 8))
    slots = list(db.scalars(select(Slot).where(Slot.turf_sport_id == ts.id)))
    return {"owner": owner, "player_user": player_user, "ts": ts, "slots": slots}


def test_booking_create_and_confirm(db):
    seed = _seed(db)
    slot_ids = [seed["slots"][0].id, seed["slots"][1].id]

    result = booking_service.create_booking(db, seed["player_user"].id, seed["ts"].id, slot_ids)
    assert result["razorpay_order_id"] == "order_test_123"
    assert result["amount"] == 104000

    booking = booking_service.confirm_booking(db, "order_test_123", "pay_test_999")
    assert booking is not None
    assert booking.status == BookingStatus.confirmed
    assert booking.payment_status == PaymentStatus.captured
    assert booking.razorpay_payment_id == "pay_test_999"

    for slot in db.scalars(select(Slot).where(Slot.id.in_(slot_ids))):
        assert slot.status == SlotStatus.booked
        assert slot.booking_id == booking.id

    payout = db.scalar(select(Payment).where(Payment.type == PaymentType.payout))
    assert payout is not None
    assert payout.status == PaymentStatus.pending
    assert float(payout.amount) == 1960.0


def test_confirm_is_idempotent(db):
    seed = _seed(db)
    booking_service.create_booking(db, seed["player_user"].id, seed["ts"].id, [seed["slots"][0].id])
    booking_service.confirm_booking(db, "order_test_123", "pay_1")
    booking_service.confirm_booking(db, "order_test_123", "pay_1")
    payouts = list(db.scalars(select(Payment).where(Payment.type == PaymentType.payout)))
    assert len(payouts) == 1


def test_double_booking_rejected(db):
    seed = _seed(db)
    slot_id = seed["slots"][0].id
    booking_service.create_booking(db, seed["player_user"].id, seed["ts"].id, [slot_id])
    booking_service.confirm_booking(db, "order_test_123", "pay_1")

    from app.exceptions import Conflict

    with pytest.raises(Conflict):
        booking_service.create_booking(db, seed["player_user"].id, seed["ts"].id, [slot_id])
