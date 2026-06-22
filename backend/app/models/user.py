from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import TimestampMixin, gen_uuid
from app.extensions import Base


class UserRole(str, enum.Enum):
    saas_admin = "saas_admin"
    turf_owner = "turf_owner"
    player = "player"


class KycStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class SubscriptionStatus(str, enum.Enum):
    inactive = "inactive"
    active = "active"
    expired = "expired"


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_phone", "phone", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    admin_profile: Mapped["SaasAdminProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    owner_profile: Mapped["TurfOwnerProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    player_profile: Mapped["Player"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class SaasAdminProfile(Base, TimestampMixin):
    __tablename__ = "saas_admin_profile"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    permissions_json: Mapped[dict] = mapped_column(MySQLJSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="admin_profile")


class TurfOwnerProfile(Base, TimestampMixin):
    __tablename__ = "turf_owner_profile"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gst_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(34), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(11), nullable=True)
    razorpay_contact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    razorpay_fund_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payout_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    kyc_status: Mapped[KycStatus] = mapped_column(Enum(KycStatus), default=KycStatus.pending, nullable=False)
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.inactive, nullable=False
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="owner_profile")


class Player(Base, TimestampMixin):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    preferred_sports: Mapped[list] = mapped_column(MySQLJSON, default=list)
    profile_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped["User"] = relationship(back_populates="player_profile")
