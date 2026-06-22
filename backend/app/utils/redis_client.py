from __future__ import annotations

from app.config import settings
from app.extensions import redis_client


def refresh_token_key(token_hash: str) -> str:
    return f"refresh_token:{token_hash}"


def password_reset_key(token: str) -> str:
    return f"password_reset:{token}"


def slot_lock_key(slot_id: str) -> str:
    return f"slot_lock:{slot_id}"


def processed_key(payment_id: str) -> str:
    return f"processed:{payment_id}"


def store_refresh_token(token_hash: str, user_id: str) -> None:
    redis_client.set(refresh_token_key(token_hash), user_id, ex=settings.REFRESH_TOKEN_TTL_DAYS * 86400)


def get_refresh_token_owner(token_hash: str) -> str | None:
    return redis_client.get(refresh_token_key(token_hash))


def revoke_refresh_token(token_hash: str) -> None:
    redis_client.delete(refresh_token_key(token_hash))


def store_password_reset(token: str, user_id: str) -> None:
    redis_client.set(password_reset_key(token), user_id, ex=settings.PASSWORD_RESET_TTL_SECONDS)


def consume_password_reset(token: str) -> str | None:
    key = password_reset_key(token)
    user_id = redis_client.get(key)
    if user_id:
        redis_client.delete(key)
    return user_id


def acquire_slot_lock(slot_id: str, player_id: str) -> bool:
    return bool(
        redis_client.set(slot_lock_key(slot_id), player_id, nx=True, ex=settings.SLOT_LOCK_TTL_SECONDS)
    )


def get_slot_lock_owner(slot_id: str) -> str | None:
    return redis_client.get(slot_lock_key(slot_id))


def release_slot_lock(slot_id: str) -> None:
    redis_client.delete(slot_lock_key(slot_id))


def mark_processed(payment_id: str, ttl: int = 86400) -> bool:
    return bool(redis_client.set(processed_key(payment_id), "1", nx=True, ex=ttl))
