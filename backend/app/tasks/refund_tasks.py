from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.extensions import db_session
from app.models.booking import Booking, Payment, PaymentStatus, PaymentType
from app.models.user import Player
from app.services import razorpay_service, whatsapp_service
from app.tasks import celery_app

_RETRY_DELAYS = [300, 1800, 7200]


@celery_app.task(name="app.tasks.refund_tasks.process_refund", bind=True, max_retries=3)
def process_refund(self, booking_id: str):
    booking = db_session.get(Booking, booking_id)
    if not booking or not booking.razorpay_payment_id or not booking.refund_amount:
        return
    if booking.refund_status == "processed":
        return

    amount_paise = int(Decimal(booking.refund_amount) * 100)
    if amount_paise <= 0:
        return

    try:
        refund = razorpay_service.create_refund(
            booking.razorpay_payment_id,
            amount_paise,
            notes={"booking_code": booking.booking_code},
        )
    except Exception as exc:  # noqa: BLE001
        delay = _RETRY_DELAYS[min(self.request.retries, len(_RETRY_DELAYS) - 1)]
        raise self.retry(exc=exc, countdown=delay)

    booking.razorpay_refund_id = refund.get("id")
    booking.refund_status = "processed"
    payment = db_session.scalar(
        select(Payment).where(
            Payment.booking_id == booking.id, Payment.type == PaymentType.refund
        )
    )
    if payment:
        payment.status = PaymentStatus.refunded
    db_session.commit()

    player = db_session.get(Player, booking.player_id)
    if player:
        whatsapp_service.send_template(
            db_session,
            player.phone,
            "turf_refund_processed",
            {
                "player_name": player.name,
                "booking_code": booking.booking_code,
                "refund_amount": str(booking.refund_amount),
                "transaction_id": booking.razorpay_refund_id or "",
            },
            tenant_id=booking.tenant_id,
        )
