from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models import TimestampMixin, gen_uuid, utcnow
from app.extensions import Base


class NotificationProvider(str, enum.Enum):
    twofactor = "2factor"
    gupshup = "gupshup"
    twilio = "twilio"


class DailyAnalytics(Base):
    __tablename__ = "daily_analytics"
    __table_args__ = (Index("ix_daily_analytics_date", "date", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_bookings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_revenue: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_platform_fees: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_owner_payouts: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    active_turfs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_players: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    old_values_json: Mapped[dict] = mapped_column(MySQLJSON, default=dict)
    new_values_json: Mapped[dict] = mapped_column(MySQLJSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = (
        Index("ix_notification_logs_tenant_id", "tenant_id"),
        Index("ix_notification_logs_recipient", "recipient_phone"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    variables_json: Mapped[dict] = mapped_column(MySQLJSON, default=dict)
    provider: Mapped[NotificationProvider] = mapped_column(Enum(NotificationProvider), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    response_json: Mapped[dict] = mapped_column(MySQLJSON, default=dict)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
