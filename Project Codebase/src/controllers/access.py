# src/controllers/access.py
from functools import wraps
from flask import abort
from flask_login import current_user, login_required

def role_required(*roles):
    """Allow access only if current_user.role is in roles."""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if not hasattr(current_user, "role") or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

def staff_or_admin_required(f):
    """Helper for routes restricted to staff/admin."""
    return role_required("staff", "admin")(f)

def admin_required(f):
    """Helper for admin-only routes."""
    return role_required("admin")(f)
