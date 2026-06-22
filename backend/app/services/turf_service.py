from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import Conflict, NotFound, ValidationFailed
from app.models.slot import Slot, SlotBlock, SlotBlockReason, SlotStatus
from app.models.sport import Sport, TurfSport
from app.models.turf import Turf
from app.schemas.turf import (
    BulkBlockSchema,
    SlotBlockSchema,
    TurfCreateSchema,
    TurfSportCreateSchema,
    TurfSportUpdateSchema,
    TurfUpdateSchema,
)
from app.utils import redis_client as rc
from app.utils.helpers import model_to_dict, serialize

_WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def serialize_turf(db: Session, turf: Turf) -> dict:
    rows = db.execute(
        select(TurfSport, Sport)
        .join(Sport, Sport.id == TurfSport.sport_id)
        .where(TurfSport.turf_id == turf.id, TurfSport.is_active.is_(True))
    ).all()
    sports = [
        {
            "id": ts.id,
            "sport_id": ts.sport_id,
            "sport_name": sport.name,
            "icon_url": sport.icon_url,
            "price_per_hour": serialize(ts.price_per_hour),
            "advance_deposit_percentage": ts.advance_deposit_percentage,
            "min_players": ts.min_players,
            "max_players": ts.max_players,
            "default_duration_minutes": sport.default_duration_minutes,
        }
        for ts, sport in rows
    ]
    data = model_to_dict(turf)
    data["sports"] = sports
    prices = [s["price_per_hour"] for s in sports]
    data["min_price_per_hour"] = min(prices) if prices else None
    return data


def _parse_time(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


def create_turf(db: Session, tenant_id: str, data: TurfCreateSchema, image_keys: list[str]) -> Turf:
    turf = Turf(
        tenant_id=tenant_id,
        name=data.name,
        address=data.address,
        city=data.city,
        latitude=data.latitude,
        longitude=data.longitude,
        description=data.description,
        amenities=data.amenities,
        images=image_keys,
        operating_hours={k: v.model_dump() for k, v in data.operating_hours.items()},
        is_active=True,
    )
    db.add(turf)
    db.commit()
    db.refresh(turf)
    return turf


def list_turfs(db: Session, tenant_id: str) -> list[Turf]:
    return list(db.scalars(select(Turf).where(Turf.tenant_id == tenant_id).order_by(Turf.created_at.desc())))


def get_owned_turf(db: Session, tenant_id: str, turf_id: str) -> Turf:
    turf = db.get(Turf, turf_id)
    if not turf or turf.tenant_id != tenant_id:
        raise NotFound("Turf not found")
    return turf


def update_turf(db: Session, tenant_id: str, turf_id: str, data: TurfUpdateSchema) -> Turf:
    turf = get_owned_turf(db, tenant_id, turf_id)
    payload = data.model_dump(exclude_unset=True)
    if "operating_hours" in payload and payload["operating_hours"] is not None:
        payload["operating_hours"] = {
            k: v.model_dump() for k, v in data.operating_hours.items()
        }
    if "amenities" in payload and payload["amenities"] is None:
        payload.pop("amenities")
    for field, value in payload.items():
        setattr(turf, field, value)
    db.commit()
    db.refresh(turf)
    return turf


def soft_delete_turf(db: Session, tenant_id: str, turf_id: str) -> None:
    turf = get_owned_turf(db, tenant_id, turf_id)
    turf.is_active = False
    db.commit()


def append_turf_images(db: Session, turf: Turf, image_keys: list[str]) -> Turf:
    turf.images = list(turf.images or []) + image_keys
    db.commit()
    db.refresh(turf)
    return turf


def list_turf_sports(db: Session, tenant_id: str, turf_id: str) -> list[TurfSport]:
    get_owned_turf(db, tenant_id, turf_id)
    return list(
        db.scalars(select(TurfSport).where(TurfSport.tenant_id == tenant_id, TurfSport.turf_id == turf_id))
    )


def _get_or_create_sport(db: Session, tenant_id: str, data: TurfSportCreateSchema) -> Sport:
    if data.sport_id:
        sport = db.get(Sport, data.sport_id)
        if not sport or sport.tenant_id != tenant_id:
            raise NotFound("Sport not found")
        return sport
    sport = db.scalar(
        select(Sport).where(Sport.tenant_id == tenant_id, Sport.name == data.sport_name)
    )
    if sport:
        return sport
    sport = Sport(
        tenant_id=tenant_id,
        name=data.sport_name,
        icon_url=data.icon_url,
        default_duration_minutes=data.default_duration_minutes,
    )
    db.add(sport)
    db.flush()
    return sport


def add_turf_sport(db: Session, tenant_id: str, turf_id: str, data: TurfSportCreateSchema) -> TurfSport:
    get_owned_turf(db, tenant_id, turf_id)
    if data.max_players < data.min_players:
        raise ValidationFailed("max_players must be >= min_players")
    sport = _get_or_create_sport(db, tenant_id, data)
    existing = db.scalar(
        select(TurfSport).where(
            TurfSport.tenant_id == tenant_id,
            TurfSport.turf_id == turf_id,
            TurfSport.sport_id == sport.id,
        )
    )
    if existing:
        raise Conflict("Sport already configured for this turf")
    turf_sport = TurfSport(
        tenant_id=tenant_id,
        turf_id=turf_id,
        sport_id=sport.id,
        price_per_hour=data.price_per_hour,
        advance_deposit_percentage=data.advance_deposit_percentage,
        min_players=data.min_players,
        max_players=data.max_players,
    )
    db.add(turf_sport)
    db.commit()
    db.refresh(turf_sport)
    return turf_sport


def get_owned_turf_sport(db: Session, tenant_id: str, turf_sport_id: str) -> TurfSport:
    turf_sport = db.get(TurfSport, turf_sport_id)
    if not turf_sport or turf_sport.tenant_id != tenant_id:
        raise NotFound("Turf sport not found")
    return turf_sport


def update_turf_sport(
    db: Session, tenant_id: str, turf_id: str, turf_sport_id: str, data: TurfSportUpdateSchema
) -> TurfSport:
    turf_sport = get_owned_turf_sport(db, tenant_id, turf_sport_id)
    if turf_sport.turf_id != turf_id:
        raise NotFound("Turf sport not found")
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(turf_sport, field, value)
    if turf_sport.max_players < turf_sport.min_players:
        raise ValidationFailed("max_players must be >= min_players")
    db.commit()
    db.refresh(turf_sport)
    return turf_sport


def build_day_slots(open_t: time, close_t: time, duration_minutes: int) -> list[tuple[time, time]]:
    slots: list[tuple[time, time]] = []
    anchor = date(2000, 1, 1)
    cursor = datetime.combine(anchor, open_t)
    end = datetime.combine(anchor, close_t)
    step = timedelta(minutes=duration_minutes)
    while cursor + step <= end:
        nxt = cursor + step
        slots.append((cursor.time(), nxt.time()))
        cursor = nxt
    return slots


def generate_slots(
    db: Session, tenant_id: str, turf_sport_id: str, days: int = 14, start_date: date | None = None
) -> int:
    turf_sport = get_owned_turf_sport(db, tenant_id, turf_sport_id)
    turf = db.get(Turf, turf_sport.turf_id)
    sport = db.get(Sport, turf_sport.sport_id)
    duration = sport.default_duration_minutes if sport else 60
    operating_hours: dict = turf.operating_hours or {}
    start = start_date or date.today()

    existing_rows = db.execute(
        select(Slot.slot_date, Slot.start_time).where(
            Slot.turf_sport_id == turf_sport_id,
            Slot.slot_date >= start,
            Slot.slot_date < start + timedelta(days=days),
        )
    ).all()
    existing = {(r[0], r[1]) for r in existing_rows}

    created = 0
    for offset in range(days):
        slot_date = start + timedelta(days=offset)
        day_key = _WEEKDAY_KEYS[slot_date.weekday()]
        hours = operating_hours.get(day_key)
        if not hours:
            continue
        for start_t, end_t in build_day_slots(
            _parse_time(hours["open"]), _parse_time(hours["close"]), duration
        ):
            if (slot_date, start_t) in existing:
                continue
            db.add(
                Slot(
                    tenant_id=tenant_id,
                    turf_sport_id=turf_sport_id,
                    slot_date=slot_date,
                    start_time=start_t,
                    end_time=end_t,
                    status=SlotStatus.available,
                )
            )
            created += 1
    db.commit()
    return created


def _emit_slot_event(event: str, turf_sport_id: str, slot_date: date, payload: dict) -> None:
    try:
        from app.extensions import socketio

        room = f"slot_{turf_sport_id}_{slot_date.isoformat()}"
        socketio.emit(event, payload, to=room)
    except Exception:  # noqa: BLE001
        pass


def block_slots(db: Session, tenant_id: str, created_by: str, data: SlotBlockSchema) -> int:
    turf_sport = get_owned_turf_sport(db, tenant_id, data.turf_sport_id)
    start_t = _parse_time(data.start_time)
    end_t = _parse_time(data.end_time)
    if end_t <= start_t:
        raise ValidationFailed("end_time must be after start_time")
    reason = SlotBlockReason(data.reason)

    slots = list(
        db.scalars(
            select(Slot).where(
                Slot.turf_sport_id == turf_sport.id,
                Slot.slot_date == data.slot_date,
                Slot.start_time >= start_t,
                Slot.start_time < end_t,
            )
        )
    )
    if any(s.status == SlotStatus.booked for s in slots):
        raise Conflict("Cannot block a slot that is already booked")

    for slot in slots:
        slot.status = SlotStatus.blocked
        slot.blocked_reason = reason.value
        rc.release_slot_lock(slot.id)

    db.add(
        SlotBlock(
            tenant_id=tenant_id,
            turf_sport_id=turf_sport.id,
            slot_date=data.slot_date,
            start_time=start_t,
            end_time=end_t,
            reason=reason,
            notes=data.notes,
            created_by=created_by,
        )
    )
    db.commit()
    for slot in slots:
        _emit_slot_event(
            "slot_blocked", turf_sport.id, data.slot_date, {"slot_id": slot.id, "reason": reason.value}
        )
    return len(slots)


def unblock_slot(db: Session, tenant_id: str, slot_id: str) -> Slot:
    slot = db.get(Slot, slot_id)
    if not slot or slot.tenant_id != tenant_id:
        raise NotFound("Slot not found")
    if slot.status not in (SlotStatus.blocked, SlotStatus.maintenance):
        raise ValidationFailed("Slot is not blocked")
    slot.status = SlotStatus.available
    slot.blocked_reason = None
    db.commit()
    _emit_slot_event("slot_available", slot.turf_sport_id, slot.slot_date, {"slot_id": slot.id})
    return slot


def bulk_block_slots(db: Session, tenant_id: str, created_by: str, data: BulkBlockSchema) -> int:
    turf_sport = get_owned_turf_sport(db, tenant_id, data.turf_sport_id)
    start_t = _parse_time(data.start_time)
    end_t = _parse_time(data.end_time)
    if end_t <= start_t:
        raise ValidationFailed("end_time must be after start_time")
    if data.end_date < data.start_date:
        raise ValidationFailed("end_date must be on or after start_date")
    reason = SlotBlockReason(data.reason)
    days = set(data.days_of_week)

    total = 0
    cursor = data.start_date
    while cursor <= data.end_date:
        if cursor.weekday() in days:
            slots = list(
                db.scalars(
                    select(Slot).where(
                        Slot.turf_sport_id == turf_sport.id,
                        Slot.slot_date == cursor,
                        Slot.start_time >= start_t,
                        Slot.start_time < end_t,
                        Slot.status == SlotStatus.available,
                    )
                )
            )
            for slot in slots:
                slot.status = SlotStatus.blocked
                slot.blocked_reason = reason.value
                rc.release_slot_lock(slot.id)
            if slots:
                db.add(
                    SlotBlock(
                        tenant_id=tenant_id,
                        turf_sport_id=turf_sport.id,
                        slot_date=cursor,
                        start_time=start_t,
                        end_time=end_t,
                        reason=reason,
                        notes=data.notes,
                        created_by=created_by,
                    )
                )
            total += len(slots)
        cursor += timedelta(days=1)
    db.commit()
    return total


def get_calendar_slots(
    db: Session, tenant_id: str, turf_id: str, sport_id: str, slot_date: date
) -> list[Slot]:
    turf_sport = db.scalar(
        select(TurfSport).where(
            TurfSport.tenant_id == tenant_id,
            TurfSport.turf_id == turf_id,
            TurfSport.sport_id == sport_id,
        )
    )
    if not turf_sport:
        raise NotFound("Turf sport not found")
    return list(
        db.scalars(
            select(Slot)
            .where(Slot.turf_sport_id == turf_sport.id, Slot.slot_date == slot_date)
            .order_by(Slot.start_time)
        )
    )
