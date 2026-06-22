from __future__ import annotations

from functools import wraps

from flask import g

from app.exceptions import Forbidden
from app.models.user import UserRole


def tenant_isolation(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if user is None:
            raise Forbidden("Authentication required for tenant-scoped resource")
        if user.role != UserRole.turf_owner:
            raise Forbidden("Tenant isolation applies to turf owners only")
        g.tenant_id = user.id
        return fn(*args, **kwargs)

    return wrapper
