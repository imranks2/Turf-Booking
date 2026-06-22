from __future__ import annotations

from functools import wraps

from flask import g, request

from app.exceptions import Unauthorized
from app.extensions import db_session
from app.models.user import User
from app.services.auth_service import decode_access_token


def _load_user_from_request() -> User:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise Unauthorized("Missing bearer token")
    payload = decode_access_token(header[7:])
    user = db_session.get(User, payload["user_id"])
    if not user or not user.is_active:
        raise Unauthorized("Account inactive")
    g.current_user = user
    g.jwt_payload = payload
    return user


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _load_user_from_request()
        return fn(*args, **kwargs)

    return wrapper


def optional_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        g.current_user = None
        g.jwt_payload = None
        if request.headers.get("Authorization", "").startswith("Bearer "):
            _load_user_from_request()
        return fn(*args, **kwargs)

    return wrapper
