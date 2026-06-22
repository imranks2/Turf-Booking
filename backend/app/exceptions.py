from __future__ import annotations

from flask import Flask, jsonify
from pydantic import ValidationError


class AppError(Exception):
    status_code: int = 400
    error_code: str = "bad_request"
    message: str = "Bad request"

    def __init__(self, message: str | None = None, error_code: str | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message
        if error_code:
            self.error_code = error_code


class ValidationFailed(AppError):
    status_code = 422
    error_code = "validation_error"
    message = "Validation failed"

    def __init__(self, message: str | None = None, details: list | None = None):
        super().__init__(message)
        self.details = details or []


class Unauthorized(AppError):
    status_code = 401
    error_code = "unauthorized"
    message = "Authentication required"


class Forbidden(AppError):
    status_code = 403
    error_code = "forbidden"
    message = "You do not have permission to perform this action"


class NotFound(AppError):
    status_code = 404
    error_code = "not_found"
    message = "Resource not found"


class Conflict(AppError):
    status_code = 409
    error_code = "conflict"
    message = "Resource conflict"


class RateLimited(AppError):
    status_code = 429
    error_code = "rate_limited"
    message = "Too many requests"


class PaymentError(AppError):
    status_code = 402
    error_code = "payment_error"
    message = "Payment processing failed"


def _envelope(code: str, message: str, status: int, details: list | None = None):
    body: dict = {"success": False, "data": None, "error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationFailed)
    def _handle_validation_failed(err: ValidationFailed):
        return _envelope(err.error_code, err.message, err.status_code, err.details)

    @app.errorhandler(AppError)
    def _handle_app_error(err: AppError):
        return _envelope(err.error_code, err.message, err.status_code)

    @app.errorhandler(ValidationError)
    def _handle_pydantic(err: ValidationError):
        details = [
            {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in err.errors()
        ]
        return _envelope("validation_error", "Validation failed", 422, details)

    @app.errorhandler(404)
    def _handle_404(_err):
        return _envelope("not_found", "Resource not found", 404)

    @app.errorhandler(405)
    def _handle_405(_err):
        return _envelope("method_not_allowed", "Method not allowed", 405)

    @app.errorhandler(Exception)
    def _handle_unexpected(err: Exception):
        app.logger.exception("Unhandled exception: %s", err)
        return _envelope("internal_error", "An unexpected error occurred", 500)
