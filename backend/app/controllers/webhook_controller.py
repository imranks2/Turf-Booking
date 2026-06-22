from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, request
from sqlalchemy import select

from app.exceptions import Unauthorized
from app.extensions import db_session
from app.models.booking import Booking, Payment, PaymentStatus, PaymentType
from app.services import booking_service, razorpay_service
from app.utils import redis_client as rc
from app.utils.helpers import success_response

webhook_bp = Blueprint("webhooks", __name__, url_prefix="/api/v1/webhooks")


def _entity(payload: dict, key: str) -> dict:
    return payload.get(key, {}).get("entity", {})


@webhook_bp.route("/razorpay", methods=["POST"])
def razorpay_webhook():
    signature = request.headers.get("X-Razorpay-Signature", "")
    raw_body = request.get_data()
    if not razorpay_service.verify_webhook_signature(raw_body, signature):
        raise Unauthorized("Invalid webhook signature")

    body = request.get_json(silent=True) or {}
    event = body.get("event", "")
    payload = body.get("payload", {})

    dedupe_key = request.headers.get("X-Razorpay-Event-Id") or _entity(payload, "payment").get("id")
    if dedupe_key and not rc.mark_processed(dedupe_key):
        return success_response({"status": "duplicate"}, 200)

    if event == "payment.captured":
        entity = _entity(payload, "payment")
        booking = booking_service.confirm_booking(db_session, entity.get("order_id"), entity.get("id"))
        if booking:
            _enqueue_post_confirmation(booking.id)
    elif event == "payment.failed":
        entity = _entity(payload, "payment")
        booking_service.fail_booking(db_session, entity.get("order_id"), entity.get("id"))
    elif event == "refund.processed":
        _handle_refund(_entity(payload, "refund"))
    elif event in ("payout.processed", "payout.failed"):
        _handle_payout(event, _entity(payload, "payout"))

    return success_response({"status": "ok"}, 200)


def _enqueue_post_confirmation(booking_id: str) -> None:
    try:
        from app.models.booking import Payment, PaymentStatus, PaymentType
        from app.tasks.payout_tasks import process_payout
        from app.tasks.whatsapp_tasks import notify_booking_confirmed

        notify_booking_confirmed.delay(booking_id)
        payout = db_session.scalar(
            select(Payment).where(
                Payment.booking_id == booking_id,
                Payment.type == PaymentType.payout,
                Payment.status == PaymentStatus.pending,
            )
        )
        if payout:
            process_payout.delay(payout.id)
    except Exception:  # noqa: BLE001
        pass


def _handle_refund(entity: dict) -> None:
    payment_id = entity.get("payment_id")
    if not payment_id:
        return
    booking = db_session.scalar(select(Booking).where(Booking.razorpay_payment_id == payment_id))
    if not booking:
        return
    booking.refund_status = "processed"
    booking.razorpay_refund_id = entity.get("id")
    db_session.commit()


def _handle_payout(event: str, entity: dict) -> None:
    transfer_id = entity.get("id")
    payout = db_session.scalar(
        select(Payment).where(
            Payment.type == PaymentType.payout, Payment.razorpay_transfer_id == transfer_id
        )
    )
    if not payout:
        return
    payout.status = PaymentStatus.processed if event == "payout.processed" else PaymentStatus.failed
    db_session.commit()


@webhook_bp.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    from app.models.analytics import NotificationLog

    body = request.get_json(silent=True) or {}
    message_id = body.get("messageId") or body.get("message_id")
    status = body.get("status")
    if message_id and status:
        log = db_session.scalar(
            select(NotificationLog).where(NotificationLog.id == message_id)
        )
        if log:
            log.status = status
            if status.lower() == "delivered":
                log.delivered_at = datetime.now(timezone.utc)
            db_session.commit()
    return success_response({"status": "ok"}, 200)
