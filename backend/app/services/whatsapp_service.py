from __future__ import annotations

from datetime import datetime, timezone

import requests
from jinja2 import Template
from sqlalchemy.orm import Session

from app.config import settings
from app.models.analytics import NotificationLog, NotificationProvider

TEMPLATES: dict[str, str] = {
    "turf_booking_confirmed": (
        "Hi {{ player_name }}, your booking at {{ turf_name }} for {{ sport }} on "
        "{{ date }} at {{ time }} is confirmed. Code: {{ booking_code }}. Address: {{ address }}."
    ),
    "turf_kickoff_reminder": (
        "Hi {{ player_name }}, reminder: {{ sport }} at {{ turf_name }} starts at {{ time }}. "
        "Code: {{ booking_code }}. See you on the turf!"
    ),
    "turf_payment_failed": (
        "Hi {{ player_name }}, your payment for {{ turf_name }} ({{ slot_time }}) failed. "
        "Retry here: {{ retry_link }}"
    ),
    "turf_booking_cancelled": (
        "Hi {{ player_name }}, your booking at {{ turf_name }} on {{ date }} is cancelled. "
        "Refund of {{ refund_amount }} will reach you in {{ refund_days }} days."
    ),
    "turf_refund_processed": (
        "Hi {{ player_name }}, refund of {{ refund_amount }} for booking {{ booking_code }} "
        "is processed. Txn: {{ transaction_id }}."
    ),
    "turf_owner_new_booking": (
        "Hi {{ owner_name }}, new booking: {{ player_name }} booked {{ sport }} on {{ date }} "
        "at {{ time }} for {{ amount }}."
    ),
    "turf_owner_payout": (
        "Hi {{ owner_name }}, payout of {{ amount }} has been initiated on {{ date }}. "
        "Txn: {{ transaction_id }}."
    ),
}


def render_template(template_name: str, variables: dict) -> str:
    template_str = TEMPLATES.get(template_name)
    if template_str is None:
        raise ValueError(f"Unknown WhatsApp template: {template_name}")
    return Template(template_str).render(**variables)


def _dispatch(phone: str, message: str) -> tuple[NotificationProvider, str, dict]:
    if settings.GUPSHUP_API_KEY and settings.GUPSHUP_APP_NAME:
        response = requests.post(
            "https://api.gupshup.io/wa/api/v1/msg",
            headers={"apikey": settings.GUPSHUP_API_KEY},
            data={
                "channel": "whatsapp",
                "source": settings.GUPSHUP_APP_NAME,
                "destination": phone,
                "message": message,
            },
            timeout=10,
        )
        return NotificationProvider.gupshup, "sent", _safe_json(response)
    if settings.TWOFACTOR_API_KEY:
        response = requests.get(
            f"https://2factor.in/API/V1/{settings.TWOFACTOR_API_KEY}/ADDON_SERVICES/SEND/TSMS",
            params={"To": phone, "Msg": message},
            timeout=10,
        )
        return NotificationProvider.twofactor, "sent", _safe_json(response)
    return NotificationProvider.gupshup, "skipped", {"reason": "provider_not_configured"}


def _safe_json(response: requests.Response) -> dict:
    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "text": response.text[:500]}


def send_template(
    db: Session,
    phone: str,
    template_name: str,
    variables: dict,
    tenant_id: str | None = None,
) -> str:
    message = render_template(template_name, variables)
    log = NotificationLog(
        tenant_id=tenant_id,
        recipient_phone=phone,
        template_name=template_name,
        variables_json=variables,
        provider=NotificationProvider.gupshup,
        status="queued",
    )
    db.add(log)
    db.flush()
    try:
        provider, status, response = _dispatch(phone, message)
        log.provider = provider
        log.status = status
        log.response_json = response
        if status == "sent":
            log.sent_at = datetime.now(timezone.utc)
    except Exception as exc:  # noqa: BLE001
        log.status = "failed"
        log.response_json = {"error": str(exc)}
    db.commit()
    return log.id
