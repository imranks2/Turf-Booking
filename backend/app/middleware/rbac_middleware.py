from __future__ import annotations

from functools import wraps

from flask import g

from app.exceptions import Forbidden
from app.middleware.auth_middleware import _load_user_from_request
from app.models.user import UserRole


def require_role(roles: list[str | UserRole]):
    allowed = {r.value if isinstance(r, UserRole) else r for r in roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if user is None:
                user = _load_user_from_request()
            if user.role.value not in allowed:
                raise Forbidden("Insufficient role privileges")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
