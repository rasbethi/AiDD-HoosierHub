from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import List, Dict, Any

from src.models.models import Booking, DowntimeBlock, Resource


def build_slot_days(
    resource: Resource,
    *,
    days: int = 3,
    start_hour: int = 7,
    end_hour: int = 22,
    start_time: datetime | None = None,
) -> List[Dict[str, Any]]:
    """
    Return a structure describing bookable hour slots for the next `days`.
    Each slot contains status (available/limited/full/downtime) plus ISO timestamps.
    """
    if start_time is None:
        view_start = datetime.now().replace(minute=0, second=0, microsecond=0)
    else:
        view_start = start_time.replace(minute=0, second=0, microsecond=0)

    view_end = view_start + timedelta(days=days)

    bookings = (
        Booking.query
        .filter(
            Booking.resource_id == resource.id,
            Booking.start_time < view_end,
            Booking.end_time > view_start,
            Booking.status.in_(["pending", "approved"]),
        )
        .all()
    )

    downtimes = (
        DowntimeBlock.query
        .filter(
            DowntimeBlock.resource_id == resource.id,
            DowntimeBlock.start_time < view_end,
            DowntimeBlock.end_time > view_start,
        )
        .all()
    )

    slot_days: List[Dict[str, Any]] = []
    for day_offset in range(days):
        current_date = (view_start + timedelta(days=day_offset)).date()
        slots: List[Dict[str, Any]] = []

        for hour in range(start_hour, end_hour):
            slot_start = datetime.combine(current_date, time(hour, 0))
            slot_end = slot_start + timedelta(hours=1)

            if slot_end < view_start:
                continue

            status = "available"
            hint = "Available"
            overlapping_bookings = []

            # Downtime overrides every other state
            for block in downtimes:
                if block.start_time < slot_end and block.end_time > slot_start:
                    status = "downtime"
                    hint = block.reason or "Downtime"
                    break

            if status != "downtime":
                for booking in bookings:
                    if booking.start_time < slot_end and booking.end_time > slot_start:
                        overlapping_bookings.append(booking)

                booked_count = len(overlapping_bookings)
                if booked_count >= resource.capacity:
                    status = "full"
                    hint = "Fully booked — join waitlist"
                elif booked_count > 0:
                    remaining = resource.capacity - booked_count
                    status = "limited"
                    hint = f"{remaining} of {resource.capacity} spots left"

            slots.append(
                {
                    "label": slot_start.strftime("%I:%M %p"),
                    "status": status,
                    "hint": hint,
                    "start_iso": slot_start.strftime("%Y-%m-%dT%H:%M"),
                    "end_iso": slot_end.strftime("%Y-%m-%dT%H:%M"),
                }
            )

        slot_days.append(
            {
                "date_label": current_date.strftime("%A, %b %d"),
                "slots": slots,
            }
        )

    return slot_days

