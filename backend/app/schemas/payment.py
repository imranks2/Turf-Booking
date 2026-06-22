from __future__ import annotations

import re
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

_IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


class RazorpayWebhookEvent(BaseModel):
    event: str
    payload: dict


class PaymentVerifySchema(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class BankDetailsSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    account_holder_name: str = Field(min_length=2, max_length=255)
    bank_account_number: str = Field(min_length=6, max_length=34)
    bank_ifsc: str
    payout_method: str = Field(default="bank_account")

    @field_validator("bank_ifsc")
    @classmethod
    def _valid_ifsc(cls, v: str) -> str:
        v = v.upper()
        if not _IFSC_RE.match(v):
            raise ValueError("Invalid IFSC code")
        return v


class AnalyticsQuerySchema(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    group_by: str = Field(default="day")

    @field_validator("group_by")
    @classmethod
    def _valid_group(cls, v: str) -> str:
        if v not in ("day", "week", "month"):
            raise ValueError("group_by must be day, week, or month")
        return v


class PaginationSchema(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
