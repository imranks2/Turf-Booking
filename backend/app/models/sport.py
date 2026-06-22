from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import TimestampMixin, gen_uuid
from app.extensions import Base


class Sport(Base, TimestampMixin):
    __tablename__ = "sports"
    __table_args__ = (Index("ix_sports_tenant_id", "tenant_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    default_duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TurfSport(Base, TimestampMixin):
    __tablename__ = "turf_sports"
    __table_args__ = (
        Index("ix_turf_sports_tenant_id", "tenant_id"),
        Index("ix_turf_sports_turf_id", "turf_id"),
        Index("ix_turf_sports_sport_id", "sport_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    turf_id: Mapped[str] = mapped_column(String(36), ForeignKey("turfs.id"), nullable=False)
    sport_id: Mapped[str] = mapped_column(String(36), ForeignKey("sports.id"), nullable=False)
    price_per_hour: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    advance_deposit_percentage: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    min_players: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    turf: Mapped["Turf"] = relationship(back_populates="turf_sports")
    sport: Mapped["Sport"] = relationship()
