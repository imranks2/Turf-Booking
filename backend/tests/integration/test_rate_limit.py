from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest

from app import create_app
from app.config import settings
from app.extensions import Base, engine
from app.middleware import rate_limit_middleware


@pytest.fixture
def client(monkeypatch):
    Base.metadata.create_all(engine)
    counters: dict[str, int] = {}

    def fake_incr(key: str, _window: int) -> int:
        counters[key] = counters.get(key, 0) + 1
        return counters[key]

    monkeypatch.setattr(rate_limit_middleware, "_incr_window", fake_incr)
    monkeypatch.setattr(settings, "RATE_LIMIT_IP_PER_MINUTE", 3)
    app = create_app()
    yield app.test_client()
    Base.metadata.drop_all(engine)


def test_ip_rate_limit_returns_429(client):
    statuses = [client.get("/api/v1/sports").status_code for _ in range(5)]
    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] == 429
    assert statuses[4] == 429


def test_health_is_not_rate_limited(client):
    for _ in range(10):
        assert client.get("/health").status_code == 200
