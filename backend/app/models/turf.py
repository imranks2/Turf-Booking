from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import TimestampMixin, gen_uuid
from app.extensions import Base


class Turf(Base, TimestampMixin):
    __tablename__ = "turfs"
    __table_args__ = (
        Index("ix_turfs_tenant_id", "tenant_id"),
        Index("ix_turfs_city", "city"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amenities: Mapped[list] = mapped_column(MySQLJSON, default=list)
    images: Mapped[list] = mapped_column(MySQLJSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    operating_hours: Mapped[dict] = mapped_column(MySQLJSON, nullable=False)

    turf_sports: Mapped[list["TurfSport"]] = relationship(back_populates="turf")
