from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import Conflict, Unauthorized, ValidationFailed
from app.models.user import Player, SaasAdminProfile, TurfOwnerProfile, User, UserRole
from app.schemas.auth import RegisterSchema
from app.utils import redis_client as rc

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user.id,
        "role": user.role.value,
        "tenant_id": user.id if user.role == UserRole.turf_owner else None,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Unauthorized("Access token expired")
    except jwt.InvalidTokenError:
        raise Unauthorized("Invalid access token")
    if payload.get("type") != "access":
        raise Unauthorized("Invalid token type")
    return payload


def issue_refresh_token(user: User) -> str:
    token = secrets.token_urlsafe(48)
    rc.store_refresh_token(_hash_token(token), user.id)
    return token


def rotate_refresh_token(db: Session, token: str) -> tuple[User, str]:
    token_hash = _hash_token(token)
    user_id = rc.get_refresh_token_owner(token_hash)
    if not user_id:
        raise Unauthorized("Invalid or expired refresh token")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise Unauthorized("Account inactive")
    rc.revoke_refresh_token(token_hash)
    return user, issue_refresh_token(user)


def revoke_refresh_token(token: str) -> None:
    rc.revoke_refresh_token(_hash_token(token))


def register_user(db: Session, data: RegisterSchema) -> User:
    existing = db.scalar(
        select(User).where((User.email == data.email) | (User.phone == data.phone))
    )
    if existing:
        raise Conflict("Email or phone already registered")

    is_active = data.role != UserRole.turf_owner
    user = User(
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=is_active,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    if data.role == UserRole.turf_owner:
        if not data.business_name:
            raise ValidationFailed("business_name is required for turf owners")
        db.add(TurfOwnerProfile(user_id=user.id, business_name=data.business_name))
    elif data.role == UserRole.player:
        db.add(Player(user_id=user.id, name=data.name, phone=data.phone))
    else:
        db.add(SaasAdminProfile(user_id=user.id, name=data.name))

    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        raise Unauthorized("Invalid credentials")
    if not user.is_active:
        raise Unauthorized("Account is inactive or pending approval")
    return user


def create_password_reset(db: Session, email: str) -> str | None:
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        return None
    token = secrets.token_urlsafe(32)
    rc.store_password_reset(token, user.id)
    return token


def reset_password(db: Session, token: str, new_password: str) -> None:
    user_id = rc.consume_password_reset(token)
    if not user_id:
        raise ValidationFailed("Invalid or expired reset token")
    user = db.get(User, user_id)
    if not user:
        raise ValidationFailed("Invalid or expired reset token")
    user.password_hash = hash_password(new_password)
    db.commit()
