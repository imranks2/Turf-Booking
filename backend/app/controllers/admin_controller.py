from __future__ import annotations

from flask import Blueprint, g, request

from app.exceptions import NotFound, ValidationFailed
from app.extensions import db_session
from app.middleware import require_role
from app.models.booking import Payment, PaymentStatus, PaymentType
from app.schemas.payment import AnalyticsQuerySchema, PaginationSchema
from app.services import analytics_service
from app.utils.helpers import success_response

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.route("/users", methods=["GET"])
@require_role(["saas_admin"])
def list_users():
    pagination = PaginationSchema(
        page=int(request.args.get("page", 1)), limit=int(request.args.get("limit", 20))
    )
    result = analytics_service.list_users(
        db_session,
        q=request.args.get("q") or None,
        role=request.args.get("role") or None,
        status=request.args.get("status") or None,
        page=pagination.page,
        limit=pagination.limit,
    )
    return success_response(result, 200)


@admin_bp.route("/users/<user_id>/approve", methods=["PATCH"])
@require_role(["saas_admin"])
def approve_user(user_id: str):
    user = analytics_service.set_user_active(db_session, user_id, True)
    analytics_service.record_audit(
        db_session, g.current_user.id, "approve_user", "user", user_id, request.remote_addr
    )
    return success_response({"id": user.id, "is_active": user.is_active}, 200)


@admin_bp.route("/users/<user_id>/suspend", methods=["PATCH"])
@require_role(["saas_admin"])
def suspend_user(user_id: str):
    user = analytics_service.set_user_active(db_session, user_id, False)
    analytics_service.record_audit(
        db_session, g.current_user.id, "suspend_user", "user", user_id, request.remote_addr
    )
    return success_response({"id": user.id, "is_active": user.is_active}, 200)


@admin_bp.route("/analytics", methods=["GET"])
@require_role(["saas_admin"])
def analytics():
    query = AnalyticsQuerySchema(
        date_from=request.args.get("from") or None,
        date_to=request.args.get("to") or None,
    )
    return success_response(
        analytics_service.admin_analytics(db_session, query.date_from, query.date_to), 200
    )


@admin_bp.route("/payouts", methods=["GET"])
@require_role(["saas_admin"])
def payouts():
    pagination = PaginationSchema(
        page=int(request.args.get("page", 1)), limit=int(request.args.get("limit", 20))
    )
    result = analytics_service.list_payouts(
        db_session, request.args.get("status") or None, pagination.page, pagination.limit
    )
    return success_response(result, 200)


@admin_bp.route("/payouts/<payout_id>/retry", methods=["POST"])
@require_role(["saas_admin"])
def retry_payout(payout_id: str):
    payout = db_session.get(Payment, payout_id)
    if not payout or payout.type != PaymentType.payout:
        raise NotFound("Payout not found")
    if payout.status not in (PaymentStatus.failed, PaymentStatus.pending):
        raise ValidationFailed("Only failed or pending payouts can be retried")
    payout.status = PaymentStatus.pending
    db_session.commit()
    _enqueue_payout(payout_id)
    return success_response({"id": payout.id, "status": payout.status.value}, 202)


@admin_bp.route("/audit-logs", methods=["GET"])
@require_role(["saas_admin"])
def audit_logs():
    pagination = PaginationSchema(
        page=int(request.args.get("page", 1)), limit=int(request.args.get("limit", 20))
    )
    result = analytics_service.list_audit_logs(
        db_session,
        request.args.get("user_id") or None,
        request.args.get("action") or None,
        pagination.page,
        pagination.limit,
    )
    return success_response(result, 200)


def _enqueue_payout(payout_id: str) -> None:
    try:
        from app.tasks.payout_tasks import process_payout

        process_payout.delay(payout_id)
    except Exception:  # noqa: BLE001
        pass
