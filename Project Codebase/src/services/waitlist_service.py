from datetime import datetime, timezone

from flask import url_for

from src.models.models import db, Booking, Waitlist
from src.services.booking_rules import ensure_capacity
from src.services.booking_service import create_owner_booking_request
from src.services.notification_service import send_notification


def promote_waitlist_entry(resource, start_time, end_time, *, actor=None):
    """
    Automatically convert the next waitlist entry into a booking
    whenever a slot becomes available.
    """
    if not resource or not start_time or not end_time:
        return None

    entry = (
        Waitlist.query.filter(
            Waitlist.resource_id == resource.id,
            Waitlist.status == "waiting",
            Waitlist.start_time == start_time,
            Waitlist.end_time == end_time,
        )
        .order_by(
            Waitlist.position.asc().nullslast(),
            Waitlist.created_at.asc(),
        )
        .first()
    )

    if not entry:
        return None

    try:
        ensure_capacity(resource, start_time, end_time)
    except ValueError:
        return None

    auto_approve = resource.access_type == "public" or resource.owner_id == entry.user_id
    booking = Booking(
        resource_id=resource.id,
        user_id=entry.user_id,
        start_time=start_time,
        end_time=end_time,
        purpose=entry.purpose or f"Auto-booked from waitlist for {resource.title}",
        status="approved" if auto_approve else "pending",
        approved_by=(actor.id if (auto_approve and actor) else (resource.owner_id if auto_approve else None)),
        decision_at=datetime.now(timezone.utc) if auto_approve else None,
        booked_by_admin=True,
    )
    db.session.add(booking)
    db.session.flush()

    if not auto_approve:
        create_owner_booking_request(resource, booking, entry.user, entry.purpose)

    entry.status = "converted"
    entry.notified = True

    send_notification(
        entry.user,
        title=f"Spot secured for {resource.title}",
        message=(
            f"A slot opened on {start_time.strftime('%b %d, %Y %I:%M %p')} - {end_time.strftime('%I:%M %p')} "
            f"and we booked it for you automatically."
            + ( " The owner will review it shortly." if not auto_approve else "")
        ),
        notification_type="waitlist_promoted",
        related_url=url_for("booking.dashboard"),
    )

    return booking

