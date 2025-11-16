"""Database helper utilities."""

from flask import abort

from src.models.models import db


def get_or_404(model, ident):
    """Return instance by primary key or abort with 404."""
    instance = db.session.get(model, ident)
    if instance is None:
        abort(404)
    return instance

