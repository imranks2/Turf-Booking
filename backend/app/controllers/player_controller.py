from __future__ import annotations

from flask import Blueprint, g, request

from app.extensions import db_session
from app.middleware import require_auth
from app.schemas.booking import BookingCancelSchema, BookingCreateSchema
from app.schemas.turf import AvailableSlotsQuerySchema, DiscoveryQuerySchema
from app.services import booking_service, player_service
from app.utils.helpers import model_to_dict, success_response

player_bp = Blueprint("player", __name__, url_prefix="/api/v1")


def _float_arg(name: str) -> float | None:
    value = request.args.get(name)
    return float(value) if value not in (None, "") else None


@player_bp.route("/turfs", methods=["GET"])
def discover_turfs():
    amenities = request.args.getlist("amenities[]") or request.args.getlist("amenities")
    query = DiscoveryQuerySchema(
        city=request.args.get("city") or None,
        sport=request.args.get("sport") or None,
        lat=_float_arg("lat"),
        lng=_float_arg("lng"),
        radius=_float_arg("radius"),
        amenities=amenities,
        date=request.args.get("date") or None,
        price_min=_float_arg("price_min"),
        price_max=_float_arg("price_max"),
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
    )
    result = player_service.discover_turfs(db_session, query)
    return success_response(result, 200)


@player_bp.route("/turfs/<turf_id>", methods=["GET"])
def turf_detail(turf_id: str):
    return success_response(player_service.get_turf_detail(db_session, turf_id), 200)


@player_bp.route("/turfs/<turf_id>/slots", methods=["GET"])
def turf_slots(turf_id: str):
    query = AvailableSlotsQuerySchema(
        date=request.args.get("date", ""),
        sport_id=request.args.get("sport_id", ""),
    )
    slots = player_service.get_available_slots(db_session, turf_id, query.sport_id, query.date)
    return success_response(slots, 200)


@player_bp.route("/sports", methods=["GET"])
def list_sports():
    return success_response(player_service.list_sports(db_session), 200)


@player_bp.route("/cities", methods=["GET"])
def list_cities():
    return success_response(player_service.list_cities(db_session), 200)


@player_bp.route("/bookings", methods=["POST"])
@require_auth
def create_booking():
    data = BookingCreateSchema(**(request.get_json(silent=True) or {}))
    result = booking_service.create_booking(
        db_session, g.current_user.id, data.turf_sport_id, data.slot_ids
    )
    return success_response(result, 201)


@player_bp.route("/bookings", methods=["GET"])
@require_auth
def list_bookings():
    bookings = booking_service.list_player_bookings(db_session, g.current_user.id)
    return success_response([model_to_dict(b) for b in bookings], 200)


@player_bp.route("/bookings/<booking_id>", methods=["GET"])
@require_auth
def get_booking(booking_id: str):
    booking = booking_service.get_player_booking(db_session, g.current_user.id, booking_id)
    return success_response(model_to_dict(booking), 200)


@player_bp.route("/bookings/<booking_id>/cancel", methods=["POST"])
@require_auth
def cancel_booking(booking_id: str):
    data = BookingCancelSchema(**(request.get_json(silent=True) or {}))
    result = booking_service.cancel_booking(db_session, g.current_user.id, booking_id, data.reason)
    _enqueue_refund(booking_id, result)
    return success_response(result, 200)


def _enqueue_refund(booking_id: str, result: dict) -> None:
    if result["refund_status"] != "pending":
        return
    try:
        from app.tasks.refund_tasks import process_refund

        process_refund.delay(booking_id)
    except Exception:  # noqa: BLE001
        pass
