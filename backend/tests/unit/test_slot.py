from __future__ import annotations

import os
from datetime import time

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest

from app.schemas.turf import TurfCreateSchema
from app.services.turf_service import build_day_slots


def test_build_day_slots_hourly():
    slots = build_day_slots(time(6, 0), time(23, 0), 60)
    assert len(slots) == 17
    assert slots[0] == (time(6, 0), time(7, 0))
    assert slots[-1] == (time(22, 0), time(23, 0))


def test_build_day_slots_partial_trailing_dropped():
    slots = build_day_slots(time(6, 0), time(7, 30), 60)
    assert slots == [(time(6, 0), time(7, 0))]


def test_build_day_slots_custom_duration():
    slots = build_day_slots(time(9, 0), time(10, 30), 30)
    assert slots == [
        (time(9, 0), time(9, 30)),
        (time(9, 30), time(10, 0)),
        (time(10, 0), time(10, 30)),
    ]


def test_turf_schema_rejects_bad_weekday():
    with pytest.raises(Exception):
        TurfCreateSchema(
            name="Arena",
            address="MG Road",
            city="Pune",
            operating_hours={"funday": {"open": "06:00", "close": "23:00"}},
        )


def test_turf_schema_rejects_close_before_open():
    with pytest.raises(Exception):
        TurfCreateSchema(
            name="Arena",
            address="MG Road",
            city="Pune",
            operating_hours={"mon": {"open": "23:00", "close": "06:00"}},
        )


def test_turf_schema_valid():
    schema = TurfCreateSchema(
        name="Arena",
        address="MG Road",
        city="Pune",
        amenities=["parking", "washroom"],
        operating_hours={"mon": {"open": "06:00", "close": "23:00"}},
    )
    assert schema.operating_hours["mon"].open == "06:00"
