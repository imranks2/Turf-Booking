from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest

from app.exceptions import Unauthorized
from app.models.user import User, UserRole
from app.services import auth_service
from app.schemas.auth import RegisterSchema


def _make_user() -> User:
    return User(
        id="u-1",
        email="a@b.com",
        phone="+919999999999",
        password_hash=auth_service.hash_password("password123"),
        role=UserRole.turf_owner,
        is_active=True,
        is_verified=False,
    )


def test_password_hash_roundtrip():
    h = auth_service.hash_password("secret-password")
    assert h != "secret-password"
    assert auth_service.verify_password("secret-password", h)
    assert not auth_service.verify_password("wrong", h)


def test_access_token_contains_tenant_for_owner():
    token = auth_service.create_access_token(_make_user())
    payload = auth_service.decode_access_token(token)
    assert payload["user_id"] == "u-1"
    assert payload["role"] == "turf_owner"
    assert payload["tenant_id"] == "u-1"
    assert payload["type"] == "access"


def test_player_token_has_no_tenant():
    user = _make_user()
    user.role = UserRole.player
    payload = auth_service.decode_access_token(auth_service.create_access_token(user))
    assert payload["tenant_id"] is None


def test_decode_rejects_garbage():
    with pytest.raises(Unauthorized):
        auth_service.decode_access_token("not-a-token")


def test_register_schema_blocks_admin():
    with pytest.raises(Exception):
        RegisterSchema(
            email="x@y.com",
            phone="+919999999999",
            password="password123",
            role="saas_admin",
            name="X",
        )


def test_register_schema_validates_phone():
    with pytest.raises(Exception):
        RegisterSchema(
            email="x@y.com",
            phone="abc",
            password="password123",
            role="player",
            name="X",
        )
