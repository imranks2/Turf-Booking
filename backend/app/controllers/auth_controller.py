from __future__ import annotations

from flask import Blueprint, make_response, request

from app.config import settings
from app.exceptions import Unauthorized
from app.extensions import db_session
from app.schemas.auth import (
    ForgotPasswordSchema,
    LoginSchema,
    RegisterSchema,
    ResetPasswordSchema,
    UserOut,
)
from app.services import auth_service
from app.utils.helpers import success_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

_REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response, token: str):
    response.set_cookie(
        _REFRESH_COOKIE,
        token,
        max_age=settings.REFRESH_TOKEN_TTL_DAYS * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="Strict" if settings.is_production else "Lax",
        path="/api/v1/auth",
    )
    return response


@auth_bp.route("/register", methods=["POST"])
def register():
    data = RegisterSchema(**(request.get_json(silent=True) or {}))
    user = auth_service.register_user(db_session, data)
    return success_response(UserOut.model_validate(user).model_dump(), 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = LoginSchema(**(request.get_json(silent=True) or {}))
    user = auth_service.authenticate(db_session, data.email, data.password)
    access_token = auth_service.create_access_token(user)
    refresh_token = auth_service.issue_refresh_token(user)
    body, status = success_response(
        {"access_token": access_token, "user": UserOut.model_validate(user).model_dump()}, 200
    )
    return _set_refresh_cookie(make_response(body, status), refresh_token)


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise Unauthorized("Missing refresh token")
    user, new_refresh = auth_service.rotate_refresh_token(db_session, token)
    access_token = auth_service.create_access_token(user)
    body, status = success_response({"access_token": access_token}, 200)
    return _set_refresh_cookie(make_response(body, status), new_refresh)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = request.cookies.get(_REFRESH_COOKIE)
    if token:
        auth_service.revoke_refresh_token(token)
    body, status = success_response({"message": "Logged out"}, 200)
    response = make_response(body, status)
    response.delete_cookie(_REFRESH_COOKIE, path="/api/v1/auth")
    return response


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = ForgotPasswordSchema(**(request.get_json(silent=True) or {}))
    auth_service.create_password_reset(db_session, data.email)
    return success_response({"message": "If the account exists, a reset link has been sent"}, 200)


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = ResetPasswordSchema(**(request.get_json(silent=True) or {}))
    auth_service.reset_password(db_session, data.token, data.new_password)
    return success_response({"message": "Password updated"}, 200)
