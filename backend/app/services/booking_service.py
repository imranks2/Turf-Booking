from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import Conflict, NotFound, ValidationFailed
from app.models.booking import Booking, BookingStatus, Payment, PaymentStatus, PaymentType
from app.models.slot import Slot, SlotStatus
from app.models.sport import TurfSport
from app.models.user import Player
from app.services import payment_service, razorpay_service
from app.utils import redis_client as rc
from app.utils.helpers import generate_booking_code


def _resolve_player(db: Session, user_id: str) -> Player:
    player = db.scalar(select(Player).where(Player.user_id == user_id))
    if not player:
        raise NotFound("Player profile not found")
    return player


def _slot_hours(slots: list[Slot]) -> Decimal:
    minutes = 0
    anchor = date(2000, 1, 1)
    for slot in slots:
        delta = datetime.combine(anchor, slot.end_time) - datetime.combine(anchor, slot.start_time)
        minutes += int(delta.total_seconds() // 60)
    return Decimal(minutes) / Decimal(60)


def _unique_booking_code(db: Session) -> str:
    for _ in range(10):
        code = generate_booking_code()
        if not db.scalar(select(Booking.id).where(Booking.booking_code == code)):
            return code
    raise Conflict("Could not allocate booking code")


def create_booking(db: Session, user_id: str, turf_sport_id: str, slot_ids: list[str]) -> dict:
    if not slot_ids:
        raise ValidationFailed("At least one slot is required")

    player = _resolve_player(db, user_id)
    turf_sport = db.get(TurfSport, turf_sport_id)
    if not turf_sport or not turf_sport.is_active:
        raise NotFound("Turf sport not found")

    slots = list(
        db.scalars(
            select(Slot)
            .where(Slot.id.in_(slot_ids), Slot.turf_sport_id == turf_sport_id)
            .with_for_update()
        )
    )
    if len(slots) != len(set(slot_ids)):
        raise ValidationFailed("One or more slots are invalid for this turf sport")
    if any(s.status != SlotStatus.available for s in slots):
        raise Conflict("One or more slots are no longer available")

    locked: list[str] = []
    for slot in slots:
        owner = rc.get_slot_lock_owner(slot.id)
        if owner is None:
            if not rc.acquire_slot_lock(slot.id, player.id):
                _release(locked)
                raise Conflict("Slot was just locked by another player")
            locked.append(slot.id)
        elif owner != player.id:
            _release(locked)
            raise Conflict("One or more slots are locked by another player")

    hours = _slot_hours(slots)
    pricing = payment_service.compute_pricing(
        Decimal(turf_sport.price_per_hour), hours, turf_sport.advance_deposit_percentage
    )

    booking_code = _unique_booking_code(db)
    booking = Booking(
        tenant_id=turf_sport.tenant_id,
        booking_code=booking_code,
        player_id=player.id,
        turf_sport_id=turf_sport_id,
        slot_ids=sorted(slot_ids),
        booking_date=min(s.slot_date for s in slots),
        total_amount=pricing["total_price"],
        advance_deposit_amount=pricing["advance_deposit_amount"],
        platform_fee=pricing["platform_fee"],
        owner_payout_amount=pricing["owner_payout_amount"],
        status=BookingStatus.pending_payment,
        payment_status=PaymentStatus.created,
    )
    db.add(booking)
    db.flush()

    order = razorpay_service.create_order(
        pricing["order_amount_paise"],
        receipt=booking_code,
        notes={"booking_id": booking.id, "player_id": player.id},
    )
    booking.razorpay_order_id = order["id"]

    db.add(
        Payment(
            tenant_id=turf_sport.tenant_id,
            booking_id=booking.id,
            amount=pricing["payable_now"],
            type=PaymentType.advance,
            razorpay_order_id=order["id"],
            status=PaymentStatus.created,
            metadata_json={
                "convenience_fee": str(pricing["convenience_fee"]),
                "advance_deposit_amount": str(pricing["advance_deposit_amount"]),
            },
        )
    )
    db.commit()
    db.refresh(booking)
    return {
        "booking_id": booking.id,
        "booking_code": booking.booking_code,
        "razorpay_order_id": order["id"],
        "amount": pricing["order_amount_paise"],
        "currency": "INR",
    }


def _release(slot_ids: list[str]) -> None:
    for slot_id in slot_ids:
        rc.release_slot_lock(slot_id)


def confirm_booking(db: Session, order_id: str, payment_id: str) -> Booking | None:
    booking = db.scalar(select(Booking).where(Booking.razorpay_order_id == order_id))
    if not booking:
        return None
    if booking.status == BookingStatus.confirmed:
        return booking

    slots = list(db.scalars(select(Slot).where(Slot.id.in_(booking.slot_ids))))
    for slot in slots:
        slot.status = SlotStatus.booked
        slot.booking_id = booking.id
        rc.release_slot_lock(slot.id)

    booking.status = BookingStatus.confirmed
    booking.payment_status = PaymentStatus.captured
    booking.razorpay_payment_id = payment_id

    advance = db.scalar(
        select(Payment).where(
            Payment.booking_id == booking.id, Payment.type == PaymentType.advance
        )
    )
    if advance:
        advance.status = PaymentStatus.captured
        advance.razorpay_payment_id = payment_id

    db.add(
        Payment(
            tenant_id=booking.tenant_id,
            booking_id=booking.id,
            amount=booking.owner_payout_amount,
            type=PaymentType.payout,
            status=PaymentStatus.pending,
            metadata_json={"booking_code": booking.booking_code},
        )
    )
    db.commit()
    db.refresh(booking)
    return booking


def fail_booking(db: Session, order_id: str, payment_id: str | None = None) -> Booking | None:
    booking = db.scalar(select(Booking).where(Booking.razorpay_order_id == order_id))
    if not booking:
        return None
    booking.payment_status = PaymentStatus.failed
    if payment_id:
        booking.razorpay_payment_id = payment_id
    for slot_id in booking.slot_ids:
        rc.release_slot_lock(slot_id)
    db.commit()
    return booking


def list_player_bookings(db: Session, user_id: str) -> list[Booking]:
    player = _resolve_player(db, user_id)
    return list(
        db.scalars(
            select(Booking)
            .where(Booking.player_id == player.id)
            .order_by(Booking.created_at.desc())
        )
    )


def get_player_booking(db: Session, user_id: str, booking_id: str) -> Booking:
    player = _resolve_player(db, user_id)
    booking = db.get(Booking, booking_id)
    if not booking or booking.player_id != player.id:
        raise NotFound("Booking not found")
    return booking


def _kickoff_datetime(db: Session, booking: Booking) -> datetime:
    slots = list(db.scalars(select(Slot).where(Slot.id.in_(booking.slot_ids))))
    earliest = min(slots, key=lambda s: (s.slot_date, s.start_time))
    return datetime.combine(earliest.slot_date, earliest.start_time, tzinfo=timezone.utc)


def cancel_booking(
    db: Session, user_id: str, booking_id: str, reason: str | None, now: datetime | None = None
) -> dict:
    booking = get_player_booking(db, user_id, booking_id)
    if booking.status in (BookingStatus.cancelled, BookingStatus.completed, BookingStatus.no_show):
        raise ValidationFailed(f"Booking cannot be cancelled from status '{booking.status.value}'")

    now = now or datetime.now(timezone.utc)
    refund = {"refund_percentage": 0, "refund_amount": Decimal("0.00")}
    if booking.status == BookingStatus.confirmed:
        hours_to_kickoff = payment_service.hours_until(_kickoff_datetime(db, booking), now)
        refund = payment_service.compute_refund(booking.advance_deposit_amount, hours_to_kickoff)

    slots = list(db.scalars(select(Slot).where(Slot.id.in_(booking.slot_ids))))
    for slot in slots:
        slot.status = SlotStatus.available
        slot.booking_id = None
        rc.release_slot_lock(slot.id)

    booking.status = BookingStatus.cancelled
    booking.cancellation_reason = reason
    booking.cancelled_at = now
    booking.refund_amount = refund["refund_amount"]
    booking.refund_status = "pending" if refund["refund_amount"] > 0 else "not_applicable"

    if refund["refund_amount"] > 0:
        db.add(
            Payment(
                tenant_id=booking.tenant_id,
                booking_id=booking.id,
                amount=refund["refund_amount"],
                type=PaymentType.refund,
                razorpay_payment_id=booking.razorpay_payment_id,
                status=PaymentStatus.pending,
                metadata_json={"refund_percentage": refund["refund_percentage"]},
            )
        )

    db.commit()
    db.refresh(booking)
    return {
        "booking_id": booking.id,
        "status": booking.status.value,
        "refund_amount": refund["refund_amount"],
        "refund_percentage": refund["refund_percentage"],
        "refund_status": booking.refund_status,
    }


def list_owner_bookings(
    db: Session, tenant_id: str, turf_id: str | None = None, status: str | None = None
) -> list[Booking]:
    stmt = select(Booking).where(Booking.tenant_id == tenant_id)
    if turf_id:
        sport_ids = [
            ts_id
            for (ts_id,) in db.execute(
                select(TurfSport.id).where(
                    TurfSport.tenant_id == tenant_id, TurfSport.turf_id == turf_id
                )
            ).all()
        ]
        stmt = stmt.where(Booking.turf_sport_id.in_(sport_ids or ["__none__"]))
    if status:
        stmt = stmt.where(Booking.status == BookingStatus(status))
    return list(db.scalars(stmt.order_by(Booking.created_at.desc())))


def mark_no_show(db: Session, tenant_id: str, booking_id: str) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking or booking.tenant_id != tenant_id:
        raise NotFound("Booking not found")
    if booking.status != BookingStatus.confirmed:
        raise ValidationFailed("Only confirmed bookings can be marked no-show")
    booking.status = BookingStatus.no_show
    db.commit()
    db.refresh(booking)
    return booking
