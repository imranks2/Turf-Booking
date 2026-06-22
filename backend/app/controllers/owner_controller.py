from __future__ import annotations

import json

from flask import Blueprint, g, request

from app.exceptions import ValidationFailed
from app.extensions import db_session
from app.middleware import require_role, tenant_isolation
from app.models.slot import Slot
from app.models.sport import TurfSport
from app.models.turf import Turf
from app.schemas.payment import AnalyticsQuerySchema, BankDetailsSchema
from app.schemas.turf import (
    BulkBlockSchema,
    CalendarQuerySchema,
    GenerateSlotsSchema,
    SlotBlockSchema,
    SlotUnblockSchema,
    TurfCreateSchema,
    TurfSportCreateSchema,
    TurfSportUpdateSchema,
    TurfUpdateSchema,
)
from app.services import analytics_service, booking_service, payment_service, turf_service
from app.utils.helpers import model_to_dict, success_response
from app.utils.s3_client import upload_turf_image

owner_bp = Blueprint("owner", __name__, url_prefix="/api/v1/owner")

_MAX_IMAGES = 10


def _turf_out(turf: Turf) -> dict:
    return turf_service.serialize_turf(db_session, turf)


def _turf_sport_out(ts: TurfSport) -> dict:
    return model_to_dict(ts)


def _slot_out(slot: Slot) -> dict:
    return model_to_dict(slot)


def _parse_turf_body() -> tuple[TurfCreateSchema, list]:
    files = request.files.getlist("images")
    if files:
        if len(files) > _MAX_IMAGES:
            raise ValidationFailed(f"At most {_MAX_IMAGES} images allowed")
        form = request.form.to_dict()
        for key in ("amenities", "operating_hours"):
            if key in form:
                try:
                    form[key] = json.loads(form[key])
                except json.JSONDecodeError:
                    raise ValidationFailed(f"{key} must be valid JSON")
        if form.get("latitude"):
            form["latitude"] = float(form["latitude"])
        if form.get("longitude"):
            form["longitude"] = float(form["longitude"])
        return TurfCreateSchema(**form), files
    return TurfCreateSchema(**(request.get_json(silent=True) or {})), []


@owner_bp.route("/turfs", methods=["GET"])
@require_role(["turf_owner"])
@tenant_isolation
def list_turfs():
    turfs = turf_service.list_turfs(db_session, g.tenant_id)
    return success_response([_turf_out(t) for t in turfs], 200)


@owner_bp.route("/turfs", methods=["POST"])
@require_role(["turf_owner"])
@tenant_isolation
def create_turf():
    data, files = _parse_turf_body()
    turf = turf_service.create_turf(db_session, g.tenant_id, data, [])
    if files:
        keys = [upload_turf_image(turf.id, f) for f in files]
        turf = turf_service.append_turf_images(db_session, turf, keys)
    return success_response(_turf_out(turf), 201)


@owner_bp.route("/turfs/<turf_id>", methods=["PUT"])
@require_role(["turf_owner"])
@tenant_isolation
def update_turf(turf_id: str):
    data = TurfUpdateSchema(**(request.get_json(silent=True) or {}))
    turf = turf_service.update_turf(db_session, g.tenant_id, turf_id, data)
    return success_response(_turf_out(turf), 200)


@owner_bp.route("/turfs/<turf_id>", methods=["DELETE"])
@require_role(["turf_owner"])
@tenant_isolation
def delete_turf(turf_id: str):
    turf_service.soft_delete_turf(db_session, g.tenant_id, turf_id)
    return success_response({"message": "Turf deactivated"}, 200)


@owner_bp.route("/turfs/<turf_id>/sports", methods=["GET"])
@require_role(["turf_owner"])
@tenant_isolation
def list_turf_sports(turf_id: str):
    sports = turf_service.list_turf_sports(db_session, g.tenant_id, turf_id)
    return success_response([_turf_sport_out(s) for s in sports], 200)


@owner_bp.route("/turfs/<turf_id>/sports", methods=["POST"])
@require_role(["turf_owner"])
@tenant_isolation
def add_turf_sport(turf_id: str):
    data = TurfSportCreateSchema(**(request.get_json(silent=True) or {}))
    turf_sport = turf_service.add_turf_sport(db_session, g.tenant_id, turf_id, data)
    return success_response(_turf_sport_out(turf_sport), 201)


@owner_bp.route("/turfs/<turf_id>/sports/<sport_id>", methods=["PUT"])
@require_role(["turf_owner"])
@tenant_isolation
def update_turf_sport(turf_id: str, sport_id: str):
    data = TurfSportUpdateSchema(**(request.get_json(silent=True) or {}))
    turf_sport = turf_service.update_turf_sport(db_session, g.tenant_id, turf_id, sport_id, data)
    return success_response(_turf_sport_out(turf_sport), 200)


@owner_bp.route("/slots", methods=["GET"])
@require_role(["turf_owner"])
@tenant_isolation
def list_slots():
    query = CalendarQuerySchema(
        turf_id=request.args.get("turf_id", ""),
        sport_id=request.args.get("sport_id", ""),
        date=request.args.get("date", ""),
    )
    slots = turf_service.get_calendar_slots(
        db_session, g.tenant_id, query.turf_id, query.sport_id, query.date
    )
    return success_response([_slot_out(s) for s in slots], 200)


@owner_bp.route("/slots/generate", methods=["POST"])
@require_role(["turf_owner"])
@tenant_isolation
def generate_slots():
    data = GenerateSlotsSchema(**(request.get_json(silent=True) or {}))
    created = turf_service.generate_slots(db_session, g.tenant_id, data.turf_sport_id, data.days)
    return success_response({"created": created}, 201)


@owner_bp.route("/slots/block", methods=["POST"])
@require_role(["turf_owner"])
@tenant_isolation
def block_slots():
    data = SlotBlockSchema(**(request.get_json(silent=True) or {}))
    blocked = turf_service.block_slots(db_session, g.tenant_id, g.current_user.id, data)
    return success_response({"blocked": blocked}, 200)


@owner_bp.route("/slots/unblock", methods=["POST"])
@require_role(["turf_owner"])
@tenant_isolation
def unblock_slot():
    data = SlotUnblockSchema(**(request.get_json(silent=True) or {}))
    slot = turf_service.unblock_slot(db_session, g.tenant_id, data.slot_id)
    return success_response(_slot_out(slot), 200)


@owner_bp.route("/slots/bulk-block", methods=["POST"])
@require_role(["turf_owner"])
@tenant_isolation
def bulk_block_slots():
    data = BulkBlockSchema(**(request.get_json(silent=True) or {}))
    blocked = turf_service.bulk_block_slots(db_session, g.tenant_id, g.current_user.id, data)
    return success_response({"blocked": blocked}, 200)


@owner_bp.route("/bookings/<booking_id>/no-show", methods=["POST"])
@require_role(["turf_owner"])
@tenant_isolation
def no_show(booking_id: str):
    booking = booking_service.mark_no_show(db_session, g.tenant_id, booking_id)
    return success_response(model_to_dict(booking), 200)


@owner_bp.route("/bookings", methods=["GET"])
@require_role(["turf_owner"])
@tenant_isolation
def list_owner_bookings():
    bookings = booking_service.list_owner_bookings(
        db_session,
        g.tenant_id,
        turf_id=request.args.get("turf_id") or None,
        status=request.args.get("status") or None,
    )
    return success_response([model_to_dict(b) for b in bookings], 200)


@owner_bp.route("/analytics", methods=["GET"])
@require_role(["turf_owner"])
@tenant_isolation
def owner_analytics():
    query = AnalyticsQuerySchema(
        date_from=request.args.get("from") or None,
        date_to=request.args.get("to") or None,
        group_by=request.args.get("group_by", "day"),
    )
    result = analytics_service.owner_analytics(db_session, g.tenant_id, query.date_from, query.date_to)
    return success_response(result, 200)


@owner_bp.route("/payouts", methods=["GET"])
@require_role(["turf_owner"])
@tenant_isolation
def owner_payouts():
    result = analytics_service.list_payouts(
        db_session,
        request.args.get("status") or None,
        int(request.args.get("page", 1)),
        int(request.args.get("limit", 20)),
        tenant_id=g.tenant_id,
    )
    return success_response(result, 200)


@owner_bp.route("/profile/bank", methods=["PUT"])
@require_role(["turf_owner"])
@tenant_isolation
def update_bank():
    data = BankDetailsSchema(**(request.get_json(silent=True) or {}))
    profile = payment_service.setup_payout_account(
        db_session,
        g.tenant_id,
        data.account_holder_name,
        data.bank_account_number,
        data.bank_ifsc,
        data.payout_method,
    )
    return success_response(
        {
            "kyc_status": profile.kyc_status.value,
            "razorpay_fund_account_id": profile.razorpay_fund_account_id,
            "payout_method": profile.payout_method,
        },
        200,
    )
