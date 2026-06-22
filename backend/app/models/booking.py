from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models import TimestampMixin, gen_uuid
from app.extensions import Base


class BookingStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class PaymentType(str, enum.Enum):
    advance = "advance"
    full = "full"
    refund = "refund"
    payout = "payout"


class PaymentStatus(str, enum.Enum):
    created = "created"
    pending = "pending"
    captured = "captured"
    failed = "failed"
    refunded = "refunded"
    processed = "processed"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_player_status", "player_id", "status"),
        Index("ix_bookings_tenant_created", "tenant_id", "created_at"),
        Index("ix_bookings_booking_code", "booking_code", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    booking_code: Mapped[str] = mapped_column(String(12), nullable=False)
    player_id: Mapped[str] = mapped_column(String(36), ForeignKey("players.id"), nullable=False)
    turf_sport_id: Mapped[str] = mapped_column(String(36), ForeignKey("turf_sports.id"), nullable=False)
    slot_ids: Mapped[list] = mapped_column(MySQLJSON, default=list)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    advance_deposit_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    owner_payout_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.pending_payment, nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.created, nullable=False
    )
    razorpay_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    refund_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    razorpay_refund_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_booking_id", "booking_id"),
        Index("ix_payments_razorpay_payment_id", "razorpay_payment_id"),
        Index("ix_payments_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    booking_id: Mapped[str] = mapped_column(String(36), ForeignKey("bookings.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    razorpay_transfer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.created, nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(MySQLJSON, default=dict)
