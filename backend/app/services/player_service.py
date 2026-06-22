from __future__ import annotations

from datetime import date
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NotFound
from app.models.slot import Slot, SlotStatus
from app.models.sport import Sport, TurfSport
from app.models.turf import Turf
from app.schemas.turf import DiscoveryQuerySchema
from app.utils.helpers import serialize

_WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return 2 * r * asin(sqrt(a))


def _turf_sports_view(db: Session, turf_id: str) -> list[dict]:
    rows = db.execute(
        select(TurfSport, Sport)
        .join(Sport, Sport.id == TurfSport.sport_id)
        .where(TurfSport.turf_id == turf_id, TurfSport.is_active.is_(True))
    ).all()
    view = []
    for ts, sport in rows:
        view.append(
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
        )
    return view


def _turf_card(turf: Turf, sports: list[dict], distance_km: float | None) -> dict:
    prices = [s["price_per_hour"] for s in sports]
    return {
        "id": turf.id,
        "name": turf.name,
        "address": turf.address,
        "city": turf.city,
        "latitude": serialize(turf.latitude),
        "longitude": serialize(turf.longitude),
        "description": turf.description,
        "amenities": turf.amenities or [],
        "images": turf.images or [],
        "sports": sports,
        "min_price_per_hour": min(prices) if prices else None,
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
    }


def discover_turfs(db: Session, q: DiscoveryQuerySchema) -> dict:
    stmt = select(Turf).where(Turf.is_active.is_(True))
    if q.city:
        stmt = stmt.where(Turf.city.ilike(q.city))

    needs_join = q.sport or q.price_min is not None or q.price_max is not None
    if needs_join:
        stmt = stmt.join(TurfSport, TurfSport.turf_id == Turf.id).where(TurfSport.is_active.is_(True))
        if q.sport:
            stmt = stmt.join(Sport, Sport.id == TurfSport.sport_id).where(Sport.name.ilike(q.sport))
        if q.price_min is not None:
            stmt = stmt.where(TurfSport.price_per_hour >= q.price_min)
        if q.price_max is not None:
            stmt = stmt.where(TurfSport.price_per_hour <= q.price_max)
        stmt = stmt.distinct()

    turfs = list(db.scalars(stmt))

    enriched: list[tuple[dict, float | None]] = []
    wanted_amenities = {a.lower() for a in q.amenities}
    weekday_key = _WEEKDAY_KEYS[q.date.weekday()] if q.date else None

    for turf in turfs:
        if wanted_amenities:
            turf_amenities = {str(a).lower() for a in (turf.amenities or [])}
            if not wanted_amenities.issubset(turf_amenities):
                continue
        if weekday_key and weekday_key not in (turf.operating_hours or {}):
            continue

        distance = None
        if q.lat is not None and q.lng is not None and turf.latitude is not None and turf.longitude is not None:
            distance = _haversine_km(q.lat, q.lng, float(turf.latitude), float(turf.longitude))
            if q.radius is not None and distance > q.radius:
                continue

        sports = _turf_sports_view(db, turf.id)
        enriched.append((_turf_card(turf, sports, distance), distance))

    if q.lat is not None and q.lng is not None:
        enriched.sort(key=lambda item: (item[1] is None, item[1] if item[1] is not None else 0.0))

    total = len(enriched)
    start = (q.page - 1) * q.limit
    page_items = [card for card, _ in enriched[start : start + q.limit]]
    return {"items": page_items, "total": total, "page": q.page, "limit": q.limit}


def get_turf_detail(db: Session, turf_id: str) -> dict:
    turf = db.get(Turf, turf_id)
    if not turf or not turf.is_active:
        raise NotFound("Turf not found")
    card = _turf_card(turf, _turf_sports_view(db, turf.id), None)
    card["operating_hours"] = turf.operating_hours or {}
    return card


def get_available_slots(db: Session, turf_id: str, sport_id: str, slot_date: date) -> list[dict]:
    turf_sport = db.scalar(
        select(TurfSport).where(
            TurfSport.turf_id == turf_id,
            TurfSport.sport_id == sport_id,
            TurfSport.is_active.is_(True),
        )
    )
    if not turf_sport:
        raise NotFound("Turf sport not found")
    slots = db.scalars(
        select(Slot)
        .where(
            Slot.turf_sport_id == turf_sport.id,
            Slot.slot_date == slot_date,
            Slot.status == SlotStatus.available,
        )
        .order_by(Slot.start_time)
    )
    return [
        {
            "id": s.id,
            "turf_sport_id": s.turf_sport_id,
            "slot_date": serialize(s.slot_date),
            "start_time": serialize(s.start_time),
            "end_time": serialize(s.end_time),
            "status": s.status.value,
        }
        for s in slots
    ]


def list_sports(db: Session) -> list[dict]:
    rows = db.execute(
        select(Sport.name, Sport.icon_url).where(Sport.is_active.is_(True)).distinct()
    ).all()
    seen: dict[str, dict] = {}
    for name, icon in rows:
        seen.setdefault(name, {"name": name, "icon_url": icon})
    return sorted(seen.values(), key=lambda s: s["name"])


def list_cities(db: Session) -> list[str]:
    rows = db.execute(select(Turf.city).where(Turf.is_active.is_(True)).distinct()).all()
    return sorted({r[0] for r in rows})
