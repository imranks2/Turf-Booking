from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

os.environ.setdefault("SECRET_KEY", "test_secret_key_0123456789_abcdef")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_0123456789_abcdef")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.services.payment_service import compute_pricing, compute_refund, hours_until


def test_pricing_two_hours_fifty_percent():
    pricing = compute_pricing(Decimal("1000"), Decimal("2"), 50)
    assert pricing["total_price"] == Decimal("2000.00")
    assert pricing["advance_deposit_amount"] == Decimal("1000.00")
    assert pricing["convenience_fee"] == Decimal("40.00")
    assert pricing["platform_fee"] == Decimal("80.00")
    assert pricing["owner_payout_amount"] == Decimal("1960.00")
    assert pricing["payable_now"] == Decimal("1040.00")
    assert pricing["order_amount_paise"] == 104000


def test_pricing_single_hour_full_deposit():
    pricing = compute_pricing(Decimal("800"), Decimal("1"), 100)
    assert pricing["advance_deposit_amount"] == Decimal("800.00")
    assert pricing["owner_payout_amount"] == Decimal("780.00")
    assert pricing["order_amount_paise"] == 82000


def test_refund_full_above_24h():
    result = compute_refund(Decimal("1000"), 30)
    assert result["refund_percentage"] == 100
    assert result["refund_amount"] == Decimal("1000.00")
    assert result["convenience_fee_refunded"] is False


def test_refund_half_between_12_and_24h():
    result = compute_refund(Decimal("1000"), 18)
    assert result["refund_percentage"] == 50
    assert result["refund_amount"] == Decimal("500.00")


def test_refund_zero_under_12h():
    result = compute_refund(Decimal("1000"), 6)
    assert result["refund_percentage"] == 0
    assert result["refund_amount"] == Decimal("0.00")


def test_refund_boundaries_inclusive():
    assert compute_refund(Decimal("1000"), 24)["refund_percentage"] == 100
    assert compute_refund(Decimal("1000"), 12)["refund_percentage"] == 50


def test_hours_until_future():
    kickoff = datetime.now(timezone.utc) + timedelta(hours=10)
    assert 9.9 < hours_until(kickoff) < 10.1
