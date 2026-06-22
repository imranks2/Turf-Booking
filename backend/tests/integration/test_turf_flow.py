from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest

from app.extensions import Base, db_session, engine
from app.models.user import User, UserRole
from app.schemas.turf import TurfCreateSchema, TurfSportCreateSchema
from app.services import auth_service, turf_service


@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    session = db_session
    yield session
    session.remove()
    Base.metadata.drop_all(engine)


def _owner(db) -> User:
    user = User(
        email="owner@turf.in",
        phone="+919812345678",
        password_hash=auth_service.hash_password("password123"),
        role=UserRole.turf_owner,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def test_turf_and_slot_generation(db):
    owner = _owner(db)
    turf = turf_service.create_turf(
        db,
        owner.id,
        TurfCreateSchema(
            name="Green Arena",
            address="MG Road",
            city="Pune",
            amenities=["parking"],
            operating_hours={
                "mon": {"open": "06:00", "close": "09:00"},
                "tue": {"open": "06:00", "close": "08:00"},
            },
        ),
        [],
    )
    assert turf.tenant_id == owner.id

    turf_sport = turf_service.add_turf_sport(
        db,
        owner.id,
        turf.id,
        TurfSportCreateSchema(sport_name="Football", price_per_hour=1200, advance_deposit_percentage=50),
    )

    monday = date(2026, 6, 8)
    created = turf_service.generate_slots(db, owner.id, turf_sport.id, days=2, start_date=monday)
    assert created == 5

    again = turf_service.generate_slots(db, owner.id, turf_sport.id, days=2, start_date=monday)
    assert again == 0

    mon_slots = turf_service.get_calendar_slots(db, owner.id, turf.id, turf_sport.sport_id, monday)
    assert len(mon_slots) == 3


def test_serialize_turf_includes_sports(db):
    owner = _owner(db)
    turf = turf_service.create_turf(
        db,
        owner.id,
        TurfCreateSchema(
            name="Serialize Arena",
            address="JM Road",
            city="Pune",
            operating_hours={"mon": {"open": "06:00", "close": "09:00"}},
        ),
        [],
    )
    turf_service.add_turf_sport(
        db, owner.id, turf.id, TurfSportCreateSchema(sport_name="Football", price_per_hour=900)
    )
    data = turf_service.serialize_turf(db, turf)
    assert isinstance(data["sports"], list)
    assert data["sports"][0]["sport_name"] == "Football"
    assert data["min_price_per_hour"] == 900.0
    assert "operating_hours" in data
    assert data["is_active"] is True


def test_tenant_isolation_blocks_foreign_turf(db):
    owner_a = _owner(db)
    turf = turf_service.create_turf(
        db,
        owner_a.id,
        TurfCreateSchema(
            name="A Turf",
            address="FC Road",
            city="Pune",
            operating_hours={"mon": {"open": "06:00", "close": "07:00"}},
        ),
        [],
    )
    from app.exceptions import NotFound

    with pytest.raises(NotFound):
        turf_service.get_owned_turf(db, "some-other-tenant", turf.id)
