from __future__ import annotations

import hashlib
import hmac

import razorpay

from app.config import settings
from app.exceptions import PaymentError

_client: razorpay.Client | None = None


def _get_client() -> razorpay.Client:
    global _client
    if _client is None:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise PaymentError("Razorpay credentials are not configured")
        _client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    return _client


def create_order(amount_paise: int, receipt: str, notes: dict | None = None) -> dict:
    try:
        return _get_client().order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "payment_capture": 1,
                "notes": notes or {},
            }
        )
    except Exception as exc:  # noqa: BLE001
        raise PaymentError(f"Failed to create Razorpay order: {exc}")


def create_refund(payment_id: str, amount_paise: int, notes: dict | None = None) -> dict:
    try:
        return _get_client().payment.refund(
            payment_id, {"amount": amount_paise, "notes": notes or {}}
        )
    except Exception as exc:  # noqa: BLE001
        raise PaymentError(f"Failed to create Razorpay refund: {exc}")


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    try:
        _get_client().utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
        return True
    except Exception:  # noqa: BLE001
        return False


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        raise PaymentError("Razorpay webhook secret is not configured")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def _razorpayx_auth() -> tuple[str, str]:
    if not settings.RAZORPAYX_KEY_ID or not settings.RAZORPAYX_KEY_SECRET:
        raise PaymentError("RazorpayX credentials are not configured")
    return settings.RAZORPAYX_KEY_ID, settings.RAZORPAYX_KEY_SECRET


def create_contact(name: str, contact_type: str = "vendor", reference_id: str | None = None) -> dict:
    import requests

    try:
        response = requests.post(
            "https://api.razorpay.com/v1/contacts",
            auth=_razorpayx_auth(),
            json={"name": name, "type": contact_type, "reference_id": reference_id},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except PaymentError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PaymentError(f"Failed to create RazorpayX contact: {exc}")


def create_fund_account(contact_id: str, account_holder_name: str, ifsc: str, account_number: str) -> dict:
    import requests

    try:
        response = requests.post(
            "https://api.razorpay.com/v1/fund_accounts",
            auth=_razorpayx_auth(),
            json={
                "contact_id": contact_id,
                "account_type": "bank_account",
                "bank_account": {
                    "name": account_holder_name,
                    "ifsc": ifsc,
                    "account_number": account_number,
                },
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except PaymentError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PaymentError(f"Failed to create RazorpayX fund account: {exc}")
