from __future__ import annotations

import secrets
import string
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any

from flask import jsonify

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_booking_code(length: int = 8) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(v) for v in value]
    return value


def model_to_dict(model: Any, exclude: set[str] | None = None) -> dict:
    exclude = exclude or set()
    columns = model.__table__.columns.keys()
    return {col: serialize(getattr(model, col)) for col in columns if col not in exclude}


def success_response(data: Any = None, status: int = 200):
    return jsonify({"success": True, "data": serialize(data), "error": None}), status
