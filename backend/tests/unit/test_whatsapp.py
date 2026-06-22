from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest

from app.services.whatsapp_service import render_template


def test_render_booking_confirmed():
    message = render_template(
        "turf_booking_confirmed",
        {
            "player_name": "Sam",
            "turf_name": "Green Arena",
            "sport": "Football",
            "date": "2026-06-08",
            "time": "06:00:00",
            "booking_code": "ABC12345",
            "address": "MG Road",
        },
    )
    assert "Sam" in message
    assert "Green Arena" in message
    assert "ABC12345" in message


def test_render_unknown_template_raises():
    with pytest.raises(ValueError):
        render_template("does_not_exist", {})
