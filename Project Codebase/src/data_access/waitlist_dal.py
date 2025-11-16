"""Waitlist entry helpers."""

from typing import List

from src.models.models import Waitlist
from src.utils.db_helpers import get_or_404


def get_waitlist_entry_or_404(entry_id: int) -> Waitlist:
    return get_or_404(Waitlist, entry_id)


def list_waiting_entries_for_user(user_id: int) -> List[Waitlist]:
    return (
        Waitlist.query
        .filter_by(user_id=user_id, status="waiting")
        .order_by(Waitlist.created_at.desc())
        .all()
    )

