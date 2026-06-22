from __future__ import annotations

import logging

from flask import Flask

from app.config import settings
from app.controllers import register_blueprints
from app.exceptions import register_error_handlers
from app.extensions import cors, db_session, socketio
from app.middleware.rate_limit_middleware import init_rate_limiting
from app.utils.helpers import success_response
from app.websocket.events import register_socket_handlers

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Permissions-Policy": "geolocation=(self), microphone=(), camera=()",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False

    logging.basicConfig(level=logging.INFO if settings.is_production else logging.DEBUG)
    logging.getLogger("geventwebsocket").setLevel(logging.WARNING)

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": settings.FRONTEND_URL}},
        supports_credentials=True,
    )
    socketio.init_app(app)

    register_error_handlers(app)
    register_blueprints(app)
    register_socket_handlers()
    init_rate_limiting(app)

    @app.route("/health")
    def health():
        return success_response({"status": "ok"}, 200)

    @app.after_request
    def _security_headers(response):
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    @app.teardown_appcontext
    def _remove_session(_exc=None):
        db_session.remove()

    return app
