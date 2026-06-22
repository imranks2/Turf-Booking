from __future__ import annotations

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NotFound
from app.models.user import KycStatus, TurfOwnerProfile

CONVENIENCE_FEE_PER_HOUR = Decimal("20")
PLATFORM_FEE_PER_HOUR = Decimal("40")


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_pricing(price_per_hour: Decimal, hours: Decimal, advance_deposit_percentage: int) -> dict:
    price_per_hour = Decimal(price_per_hour)
    hours = Decimal(hours)
    total_price = _money(price_per_hour * hours)
    advance_deposit_amount = _money(total_price * Decimal(advance_deposit_percentage) / Decimal(100))
    convenience_fee = _money(CONVENIENCE_FEE_PER_HOUR * hours)
    platform_fee = _money(PLATFORM_FEE_PER_HOUR * hours)
    owner_payout_amount = _money(total_price - CONVENIENCE_FEE_PER_HOUR * hours)
    payable_now = _money(advance_deposit_amount + convenience_fee)
    return {
        "hours": hours,
        "total_price": total_price,
        "advance_deposit_amount": advance_deposit_amount,
        "convenience_fee": convenience_fee,
        "platform_fee": platform_fee,
        "owner_payout_amount": owner_payout_amount,
        "payable_now": payable_now,
        "order_amount_paise": int(payable_now * 100),
    }


def hours_until(kickoff: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    return (kickoff - now).total_seconds() / 3600.0


def compute_refund(advance_deposit_amount: Decimal, hours_to_kickoff: float) -> dict:
    advance_deposit_amount = Decimal(advance_deposit_amount)
    if hours_to_kickoff >= 24:
        pct = Decimal("1.0")
    elif hours_to_kickoff >= 12:
        pct = Decimal("0.5")
    else:
        pct = Decimal("0.0")
    refund_amount = _money(advance_deposit_amount * pct)
    return {
        "refund_percentage": int(pct * 100),
        "refund_amount": refund_amount,
        "convenience_fee_refunded": False,
    }


def setup_payout_account(
    db: Session,
    owner_id: str,
    account_holder_name: str,
    bank_account_number: str,
    bank_ifsc: str,
    payout_method: str,
) -> TurfOwnerProfile:
    from app.services import razorpay_service

    profile = db.scalar(select(TurfOwnerProfile).where(TurfOwnerProfile.user_id == owner_id))
    if not profile:
        raise NotFound("Owner profile not found")

    if not profile.razorpay_contact_id:
        contact = razorpay_service.create_contact(profile.business_name, reference_id=owner_id)
        profile.razorpay_contact_id = contact["id"]

    fund_account = razorpay_service.create_fund_account(
        profile.razorpay_contact_id, account_holder_name, bank_ifsc, bank_account_number
    )
    profile.razorpay_fund_account_id = fund_account["id"]
    profile.bank_account_number = bank_account_number
    profile.bank_ifsc = bank_ifsc
    profile.payout_method = payout_method
    profile.kyc_status = KycStatus.verified
    db.commit()
    db.refresh(profile)
    return profile
