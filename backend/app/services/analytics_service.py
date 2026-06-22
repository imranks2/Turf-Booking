from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import NotFound
from app.models.analytics import AuditLog
from app.models.booking import Booking, BookingStatus, Payment, PaymentType
from app.models.sport import Sport, TurfSport
from app.models.user import Player, SaasAdminProfile, TurfOwnerProfile, User, UserRole

_REVENUE_STATUSES = (BookingStatus.confirmed, BookingStatus.completed)


def _range_bounds(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    end = datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
    return start, end


def _apply_range(stmt: Select, start: datetime | None, end: datetime | None) -> Select:
    if start is not None:
        stmt = stmt.where(Booking.created_at >= start)
    if end is not None:
        stmt = stmt.where(Booking.created_at <= end)
    return stmt


def owner_analytics(db: Session, tenant_id: str, date_from: date | None, date_to: date | None) -> dict:
    start, end = _range_bounds(date_from, date_to)

    totals_stmt = _apply_range(
        select(
            func.count(Booking.id),
            func.coalesce(func.sum(Booking.total_amount), 0),
            func.coalesce(func.sum(Booking.platform_fee), 0),
            func.coalesce(func.sum(Booking.owner_payout_amount), 0),
        ).where(Booking.tenant_id == tenant_id, Booking.status.in_(_REVENUE_STATUSES)),
        start,
        end,
    )
    count, revenue, platform_fees, payouts = db.execute(totals_stmt).one()

    sport_stmt = _apply_range(
        select(Sport.name, func.count(Booking.id), func.coalesce(func.sum(Booking.total_amount), 0))
        .join(TurfSport, TurfSport.id == Booking.turf_sport_id)
        .join(Sport, Sport.id == TurfSport.sport_id)
        .where(Booking.tenant_id == tenant_id, Booking.status.in_(_REVENUE_STATUSES))
        .group_by(Sport.name),
        start,
        end,
    )
    by_sport = [
        {"sport": name, "bookings": int(c), "revenue": float(rev)}
        for name, c, rev in db.execute(sport_stmt).all()
    ]

    series_stmt = _apply_range(
        select(
            func.date(Booking.created_at),
            func.count(Booking.id),
            func.coalesce(func.sum(Booking.total_amount), 0),
        )
        .where(Booking.tenant_id == tenant_id, Booking.status.in_(_REVENUE_STATUSES))
        .group_by(func.date(Booking.created_at))
        .order_by(func.date(Booking.created_at)),
        start,
        end,
    )
    time_series = [
        {"date": str(d), "bookings": int(c), "revenue": float(rev)}
        for d, c, rev in db.execute(series_stmt).all()
    ]

    return {
        "total_bookings": int(count),
        "total_revenue": float(revenue),
        "total_platform_fees": float(platform_fees),
        "total_owner_payouts": float(payouts),
        "by_sport": by_sport,
        "time_series": time_series,
    }


def admin_analytics(db: Session, date_from: date | None, date_to: date | None) -> dict:
    start, end = _range_bounds(date_from, date_to)

    totals_stmt = _apply_range(
        select(
            func.count(Booking.id),
            func.coalesce(func.sum(Booking.total_amount), 0),
            func.coalesce(func.sum(Booking.platform_fee), 0),
            func.coalesce(func.sum(Booking.owner_payout_amount), 0),
        ).where(Booking.status.in_(_REVENUE_STATUSES)),
        start,
        end,
    )
    count, revenue, platform_fees, payouts = db.execute(totals_stmt).one()

    active_owners = db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.turf_owner, User.is_active.is_(True))
    )
    active_players = db.scalar(select(func.count(Player.id)))

    series_stmt = _apply_range(
        select(
            func.date(Booking.created_at),
            func.count(Booking.id),
            func.coalesce(func.sum(Booking.platform_fee), 0),
        )
        .where(Booking.status.in_(_REVENUE_STATUSES))
        .group_by(func.date(Booking.created_at))
        .order_by(func.date(Booking.created_at)),
        start,
        end,
    )
    time_series = [
        {"date": str(d), "bookings": int(c), "platform_fees": float(pf)}
        for d, c, pf in db.execute(series_stmt).all()
    ]

    return {
        "total_bookings": int(count),
        "total_revenue": float(revenue),
        "total_platform_fees": float(platform_fees),
        "total_owner_payouts": float(payouts),
        "active_owners": int(active_owners or 0),
        "active_players": int(active_players or 0),
        "time_series": time_series,
    }


def _serialize_user(user: User, name: str | None) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "name": name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def list_users(
    db: Session,
    q: str | None,
    role: str | None,
    status: str | None,
    page: int,
    limit: int,
) -> dict:
    stmt = select(User)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.phone.ilike(like)))
    if role:
        stmt = stmt.where(User.role == UserRole(role))
    if status == "active":
        stmt = stmt.where(User.is_active.is_(True))
    elif status == "inactive":
        stmt = stmt.where(User.is_active.is_(False))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    users = list(
        db.scalars(stmt.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit))
    )

    items = []
    for user in users:
        name = None
        if user.role == UserRole.turf_owner:
            profile = db.scalar(
                select(TurfOwnerProfile).where(TurfOwnerProfile.user_id == user.id)
            )
            name = profile.business_name if profile else None
        elif user.role == UserRole.player:
            profile = db.scalar(select(Player).where(Player.user_id == user.id))
            name = profile.name if profile else None
        else:
            profile = db.scalar(select(SaasAdminProfile).where(SaasAdminProfile.user_id == user.id))
            name = profile.name if profile else None
        items.append(_serialize_user(user, name))

    return {"items": items, "total": int(total), "page": page, "limit": limit}


def set_user_active(db: Session, user_id: str, active: bool) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFound("User not found")
    user.is_active = active
    db.commit()
    db.refresh(user)
    return user


def list_payouts(
    db: Session, status: str | None, page: int, limit: int, tenant_id: str | None = None
) -> dict:
    stmt = select(Payment).where(Payment.type == PaymentType.payout)
    if tenant_id:
        stmt = stmt.where(Payment.tenant_id == tenant_id)
    if status:
        from app.models.booking import PaymentStatus

        stmt = stmt.where(Payment.status == PaymentStatus(status))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    payouts = list(
        db.scalars(stmt.order_by(Payment.created_at.desc()).offset((page - 1) * limit).limit(limit))
    )
    items = [
        {
            "id": p.id,
            "tenant_id": p.tenant_id,
            "booking_id": p.booking_id,
            "amount": float(p.amount),
            "status": p.status.value,
            "razorpay_transfer_id": p.razorpay_transfer_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payouts
    ]
    return {"items": items, "total": int(total), "page": page, "limit": limit}


def list_audit_logs(
    db: Session, user_id: str | None, action: str | None, page: int, limit: int
) -> dict:
    stmt = select(AuditLog)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    logs = list(
        db.scalars(stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit))
    )
    items = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    return {"items": items, "total": int(total), "page": page, "limit": limit}


def record_audit(
    db: Session,
    user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    ip_address: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            old_values_json=old_values or {},
            new_values_json=new_values or {},
        )
    )
    db.commit()
