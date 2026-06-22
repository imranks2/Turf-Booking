from __future__ import annotations

import os
from datetime import date, time

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest

from app.extensions import Base, db_session, engine
from app.models.slot import Slot, SlotStatus
from app.models.user import User, UserRole
from app.schemas.turf import DiscoveryQuerySchema, TurfCreateSchema, TurfSportCreateSchema
from app.services import auth_service, player_service, turf_service


@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    yield db_session
    db_session.remove()
    Base.metadata.drop_all(engine)


def _seed(db) -> dict:
    owner = User(
        email="o@t.in",
        phone="+919812345670",
        password_hash=auth_service.hash_password("password123"),
        role=UserRole.turf_owner,
        is_active=True,
    )
    db.add(owner)
    db.commit()
    turf = turf_service.create_turf(
        db,
        owner.id,
        TurfCreateSchema(
            name="Green Arena",
            address="MG Road",
            city="Pune",
            latitude=18.5204,
            longitude=73.8567,
            amenities=["parking", "washroom"],
            operating_hours={"mon": {"open": "06:00", "close": "09:00"}},
        ),
        [],
    )
    ts = turf_service.add_turf_sport(
        db, owner.id, turf.id, TurfSportCreateSchema(sport_name="Football", price_per_hour=1000)
    )
    turf_service.generate_slots(db, owner.id, ts.id, days=1, start_date=date(2026, 6, 8))
    return {"owner": owner, "turf": turf, "ts": ts}


def test_discovery_by_city_and_price(db):
    seed = _seed(db)
    result = player_service.discover_turfs(db, DiscoveryQuerySchema(city="pune", price_max=1500))
    assert result["total"] == 1
    assert result["items"][0]["id"] == seed["turf"].id
    assert result["items"][0]["min_price_per_hour"] == 1000.0

    empty = player_service.discover_turfs(db, DiscoveryQuerySchema(price_min=5000))
    assert empty["total"] == 0


def test_discovery_amenity_filter(db):
    _seed(db)
    miss = player_service.discover_turfs(db, DiscoveryQuerySchema(amenities=["pool"]))
    assert miss["total"] == 0
    hit = player_service.discover_turfs(db, DiscoveryQuerySchema(amenities=["parking"]))
    assert hit["total"] == 1


def test_available_slots_excludes_booked(db):
    seed = _seed(db)
    slots = player_service.get_available_slots(db, seed["turf"].id, seed["ts"].sport_id, date(2026, 6, 8))
    assert len(slots) == 3

    booked = db.query(Slot).filter(Slot.start_time == time(6, 0)).first()
    booked.status = SlotStatus.booked
    db.commit()

    slots_after = player_service.get_available_slots(
        db, seed["turf"].id, seed["ts"].sport_id, date(2026, 6, 8)
    )
    assert len(slots_after) == 2


def test_turf_detail_and_lookups(db):
    seed = _seed(db)
    detail = player_service.get_turf_detail(db, seed["turf"].id)
    assert detail["name"] == "Green Arena"
    assert len(detail["sports"]) == 1
    assert "operating_hours" in detail
    assert player_service.list_cities(db) == ["Pune"]
    assert [s["name"] for s in player_service.list_sports(db)] == ["Football"]
