from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from sqlalchemy import select

from app.extensions import Base, db_session, engine
from app.models.slot import Slot, SlotStatus
from app.models.user import User, UserRole
from app.schemas.turf import BulkBlockSchema, SlotBlockSchema, TurfCreateSchema, TurfSportCreateSchema
from app.services import auth_service, turf_service


@pytest.fixture
def db(monkeypatch):
    Base.metadata.create_all(engine)
    monkeypatch.setattr(turf_service.rc, "release_slot_lock", lambda _s: None)
    yield db_session
    db_session.remove()
    Base.metadata.drop_all(engine)


def _seed(db) -> dict:
    owner = User(email="o@t.in", phone="+919812345603", password_hash=auth_service.hash_password("password123"), role=UserRole.turf_owner, is_active=True)
    db.add(owner)
    db.commit()
    turf = turf_service.create_turf(db, owner.id, TurfCreateSchema(name="Arena", address="MG Road", city="Pune", operating_hours={"mon": {"open": "06:00", "close": "10:00"}}), [])
    ts = turf_service.add_turf_sport(db, owner.id, turf.id, TurfSportCreateSchema(sport_name="Football", price_per_hour=1000))
    turf_service.generate_slots(db, owner.id, ts.id, days=1, start_date=date(2026, 6, 8))
    return {"owner": owner, "ts": ts}


def test_block_range(db):
    seed = _seed(db)
    blocked = turf_service.block_slots(
        db,
        seed["owner"].id,
        seed["owner"].id,
        SlotBlockSchema(
            turf_sport_id=seed["ts"].id,
            slot_date=date(2026, 6, 8),
            start_time="06:00",
            end_time="08:00",
            reason="maintenance",
        ),
    )
    assert blocked == 2
    blocked_slots = list(
        db.scalars(select(Slot).where(Slot.status == SlotStatus.blocked))
    )
    assert len(blocked_slots) == 2
    assert all(s.blocked_reason == "maintenance" for s in blocked_slots)


def test_unblock(db):
    seed = _seed(db)
    turf_service.block_slots(
        db, seed["owner"].id, seed["owner"].id,
        SlotBlockSchema(turf_sport_id=seed["ts"].id, slot_date=date(2026, 6, 8), start_time="06:00", end_time="07:00", reason="other"),
    )
    blocked = db.scalars(select(Slot).where(Slot.status == SlotStatus.blocked)).first()
    slot = turf_service.unblock_slot(db, seed["owner"].id, blocked.id)
    assert slot.status == SlotStatus.available
    assert slot.blocked_reason is None


def test_bulk_block_by_weekday(db):
    seed = _seed(db)
    blocked = turf_service.bulk_block_slots(
        db, seed["owner"].id, seed["owner"].id,
        BulkBlockSchema(
            turf_sport_id=seed["ts"].id,
            start_date=date(2026, 6, 8),
            end_date=date(2026, 6, 8),
            days_of_week=[0],
            start_time="06:00",
            end_time="10:00",
            reason="private_event",
        ),
    )
    assert blocked == 4
