"""Booking-related database helpers."""

from typing import List

from src.models.models import Booking
from src.utils.db_helpers import get_or_404


def get_booking_or_404(booking_id: int) -> Booking:
    return get_or_404(Booking, booking_id)


def list_all_bookings() -> List[Booking]:
    return Booking.query.order_by(Booking.start_time.desc()).all()


def list_bookings_for_user(user_id: int) -> List[Booking]:
    return (
        Booking.query.filter_by(user_id=user_id)
        .order_by(Booking.start_time.desc())
        .all()
    )

