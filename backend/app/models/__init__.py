from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


from app.models.user import (  # noqa: E402
    Player,
    SaasAdminProfile,
    TurfOwnerProfile,
    User,
    UserRole,
)
from app.models.sport import Sport, TurfSport  # noqa: E402
from app.models.turf import Turf  # noqa: E402
from app.models.slot import Slot, SlotBlock, SlotBlockReason, SlotStatus  # noqa: E402
from app.models.booking import (  # noqa: E402
    Booking,
    BookingStatus,
    Payment,
    PaymentStatus,
    PaymentType,
)
from app.models.analytics import (  # noqa: E402
    AuditLog,
    DailyAnalytics,
    NotificationLog,
    NotificationProvider,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "gen_uuid",
    "utcnow",
    "User",
    "UserRole",
    "SaasAdminProfile",
    "TurfOwnerProfile",
    "Player",
    "Turf",
    "Sport",
    "TurfSport",
    "Slot",
    "SlotStatus",
    "SlotBlock",
    "SlotBlockReason",
    "Booking",
    "BookingStatus",
    "Payment",
    "PaymentType",
    "PaymentStatus",
    "DailyAnalytics",
    "AuditLog",
    "NotificationLog",
    "NotificationProvider",
]
