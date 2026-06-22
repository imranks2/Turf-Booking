from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.controllers.admin_controller import admin_bp
    from app.controllers.auth_controller import auth_bp
    from app.controllers.owner_controller import owner_bp
    from app.controllers.player_controller import player_bp
    from app.controllers.webhook_controller import webhook_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(player_bp)
    app.register_blueprint(webhook_bp)
