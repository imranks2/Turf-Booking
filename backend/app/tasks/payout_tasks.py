from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.config import settings
from app.extensions import db_session
from app.models.booking import Payment, PaymentStatus, PaymentType
from app.models.user import TurfOwnerProfile
from app.tasks import celery_app

_RETRY_DELAYS = [300, 1800, 7200]


@celery_app.task(name="app.tasks.payout_tasks.process_payout", bind=True, max_retries=3)
def process_payout(self, payment_id: str):
    payout = db_session.get(Payment, payment_id)
    if not payout or payout.type != PaymentType.payout or payout.status != PaymentStatus.pending:
        return

    owner_profile = db_session.scalar(
        select(TurfOwnerProfile).where(TurfOwnerProfile.user_id == payout.tenant_id)
    )
    if not owner_profile or owner_profile.kyc_status.value != "verified":
        payout.status = PaymentStatus.failed
        payout.metadata_json = {**(payout.metadata_json or {}), "error": "kyc_not_verified"}
        db_session.commit()
        return

    if not settings.RAZORPAYX_KEY_ID or not settings.RAZORPAYX_KEY_SECRET:
        payout.metadata_json = {**(payout.metadata_json or {}), "note": "razorpayx_not_configured"}
        db_session.commit()
        return

    try:
        amount_paise = int(Decimal(payout.amount) * 100)
        transfer = _create_razorpayx_payout(
            owner_profile.razorpay_fund_account_id, amount_paise, payout.id
        )
        payout.razorpay_transfer_id = transfer["id"]
        db_session.commit()
    except Exception as exc:  # noqa: BLE001
        delay = _RETRY_DELAYS[min(self.request.retries, len(_RETRY_DELAYS) - 1)]
        raise self.retry(exc=exc, countdown=delay)


def _create_razorpayx_payout(fund_account_id: str | None, amount_paise: int, reference: str) -> dict:
    import requests

    response = requests.post(
        "https://api.razorpay.com/v1/payouts",
        auth=(settings.RAZORPAYX_KEY_ID, settings.RAZORPAYX_KEY_SECRET),
        json={
            "fund_account_id": fund_account_id,
            "amount": amount_paise,
            "currency": "INR",
            "mode": "IMPS",
            "purpose": "payout",
            "reference_id": reference,
            "queue_if_low_balance": True,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
