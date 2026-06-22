from __future__ import annotations

from flask import Flask, request

from app.config import settings
from app.exceptions import RateLimited
from app.extensions import redis_client


def _incr_window(key: str, window_seconds: int) -> int:
    count = int(redis_client.incr(key))
    if count == 1:
        redis_client.expire(key, window_seconds)
    return count


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _enforce() -> None:
    if not request.path.startswith("/api/"):
        return
    if request.method == "OPTIONS":
        return

    try:
        ip_count = _incr_window(f"rate_limit:{_client_ip()}", 60)
    except Exception:  # noqa: BLE001
        return

    if ip_count > settings.RATE_LIMIT_IP_PER_MINUTE:
        raise RateLimited("IP rate limit exceeded")

    user_id = _user_id_from_token()
    if user_id:
        try:
            user_count = _incr_window(f"rate_limit:{user_id}", 60)
        except Exception:  # noqa: BLE001
            return
        if user_count > settings.RATE_LIMIT_USER_PER_MINUTE:
            raise RateLimited("User rate limit exceeded")


def _user_id_from_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        from app.services.auth_service import decode_access_token

        return decode_access_token(header[7:]).get("user_id")
    except Exception:  # noqa: BLE001
        return None


def init_rate_limiting(app: Flask) -> None:
    app.before_request(_enforce)
