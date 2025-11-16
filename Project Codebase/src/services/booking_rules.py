from datetime import datetime


MIN_HOURS = 1
MAX_HOURS = 10
BOOKING_CONFLICT_MESSAGE = "Resource is fully booked for this time frame. Join waitlist or choose another time."


def validate_time_block(start_time: datetime, end_time: datetime) -> None:
    """Ensure bookings use whole hours between 1 and 10 hours."""
    if start_time >= end_time:
        raise ValueError("End time must be after start time.")

    if any(
        value != 0
        for value in (
            start_time.minute,
            start_time.second,
            start_time.microsecond,
            end_time.minute,
            end_time.second,
            end_time.microsecond,
        )
    ):
        raise ValueError("Bookings must start and end on the hour.")

    duration_hours = (end_time - start_time).total_seconds() / 3600
    if duration_hours < MIN_HOURS or duration_hours > MAX_HOURS:
        raise ValueError("Bookings must be between 1 and 10 hours long.")


def ensure_capacity(resource, start_time: datetime, end_time: datetime, *, exclude_booking_id=None) -> None:
    """Raise ValueError when no slots remain for the requested window."""
    remaining = resource.get_available_slots(start_time, end_time, exclude_booking_id=exclude_booking_id)
    if remaining <= 0:
        raise ValueError(BOOKING_CONFLICT_MESSAGE)

