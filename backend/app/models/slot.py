from __future__ import annotations

import enum
from datetime import date, time

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models import TimestampMixin, gen_uuid
from app.extensions import Base


class SlotStatus(str, enum.Enum):
    available = "available"
    booked = "booked"
    blocked = "blocked"
    maintenance = "maintenance"


class SlotBlockReason(str, enum.Enum):
    offline_walkin = "offline_walkin"
    maintenance = "maintenance"
    private_event = "private_event"
    other = "other"


class Slot(Base, TimestampMixin):
    __tablename__ = "slots"
    __table_args__ = (
        Index("ix_slots_calendar", "turf_sport_id", "slot_date", "status"),
        Index("ix_slots_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    turf_sport_id: Mapped[str] = mapped_column(String(36), ForeignKey("turf_sports.id"), nullable=False)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus), default=SlotStatus.available, nullable=False)
    booking_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("bookings.id"), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class SlotBlock(Base, TimestampMixin):
    __tablename__ = "slot_blocks"
    __table_args__ = (
        Index("ix_slot_blocks_tenant_id", "tenant_id"),
        Index("ix_slot_blocks_turf_sport_id", "turf_sport_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    turf_sport_id: Mapped[str] = mapped_column(String(36), ForeignKey("turf_sports.id"), nullable=False)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    reason: Mapped[SlotBlockReason] = mapped_column(Enum(SlotBlockReason), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
