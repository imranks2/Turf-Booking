from __future__ import annotations

from sqlalchemy import select

from app.extensions import db_session
from app.models.booking import Booking
from app.models.slot import Slot
from app.models.sport import Sport, TurfSport
from app.models.turf import Turf
from app.models.user import Player, TurfOwnerProfile, User
from app.services import whatsapp_service
from app.tasks import celery_app
from app.utils.helpers import serialize


@celery_app.task(name="app.tasks.whatsapp_tasks.send_template", bind=True, max_retries=3)
def send_template(self, phone: str, template_name: str, variables: dict, tenant_id: str | None = None):
    try:
        return whatsapp_service.send_template(db_session, phone, template_name, variables, tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="app.tasks.whatsapp_tasks.notify_booking_confirmed")
def notify_booking_confirmed(booking_id: str):
    booking = db_session.get(Booking, booking_id)
    if not booking:
        return
    player = db_session.get(Player, booking.player_id)
    turf_sport = db_session.get(TurfSport, booking.turf_sport_id)
    turf = db_session.get(Turf, turf_sport.turf_id) if turf_sport else None
    sport = db_session.get(Sport, turf_sport.sport_id) if turf_sport else None
    owner = db_session.get(User, booking.tenant_id)
    owner_profile = db_session.scalar(
        select(TurfOwnerProfile).where(TurfOwnerProfile.user_id == booking.tenant_id)
    )
    earliest = db_session.scalar(
        select(Slot).where(Slot.id.in_(booking.slot_ids)).order_by(Slot.start_time)
    )
    time_str = serialize(earliest.start_time) if earliest else ""
    date_str = serialize(booking.booking_date)

    if player:
        whatsapp_service.send_template(
            db_session,
            player.phone,
            "turf_booking_confirmed",
            {
                "player_name": player.name,
                "turf_name": turf.name if turf else "",
                "sport": sport.name if sport else "",
                "date": date_str,
                "time": time_str,
                "booking_code": booking.booking_code,
                "address": turf.address if turf else "",
            },
            tenant_id=booking.tenant_id,
        )

    if owner:
        whatsapp_service.send_template(
            db_session,
            owner.phone,
            "turf_owner_new_booking",
            {
                "owner_name": owner_profile.business_name if owner_profile else "Owner",
                "player_name": player.name if player else "",
                "sport": sport.name if sport else "",
                "date": date_str,
                "time": time_str,
                "amount": str(serialize(booking.total_amount)),
            },
            tenant_id=booking.tenant_id,
        )
