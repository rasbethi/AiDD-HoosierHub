"""Encapsulated resource CRUD helpers."""

from typing import List, Optional

from src.models.models import Resource
from src.utils.db_helpers import get_or_404


def get_resource_or_404(resource_id: int) -> Resource:
    """Fetch a resource or raise 404."""
    return get_or_404(Resource, resource_id)


def list_published_resources(limit: Optional[int] = None) -> List[Resource]:
    """Return published resources, newest first."""
    query = Resource.query.filter(Resource.status == Resource.STATUS_PUBLISHED).order_by(
        Resource.created_at.desc()
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def list_resources_for_owner(owner_id: int) -> List[Resource]:
    """Return all resources owned by the specified user."""
    return (
        Resource.query.filter_by(owner_id=owner_id)
        .order_by(Resource.created_at.desc())
        .all()
    )

