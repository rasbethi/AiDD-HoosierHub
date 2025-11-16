from flask import url_for

from src.models.models import db, BookingRequest, Message
from src.services.notification_service import send_notification


def create_owner_booking_request(resource, booking, requester, purpose):
    """
    Ensure resource owners receive an actionable booking request entry
    whenever a restricted resource booking is pending their approval.
    """
    if resource.access_type == "public" or not resource.owner or resource.owner_id == requester.id:
        return None

    existing = BookingRequest.query.filter_by(booking_id=booking.id).first()
    if existing:
        return existing

    booking_request = BookingRequest(
        resource_id=resource.id,
        requester_id=requester.id,
        booking_id=booking.id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        purpose=purpose,
        status="pending",
        kind="owner"
    )
    db.session.add(booking_request)
    db.session.flush()

    message = Message(
        sender_id=requester.id,
        receiver_id=resource.owner.id,
        request_id=booking_request.id,
        subject=f"Booking request for {resource.title}",
        content=(
            f"{requester.name} requested to use {resource.title} "
            f"from {booking.start_time.strftime('%b %d, %Y %I:%M %p')} "
            f"to {booking.end_time.strftime('%b %d, %Y %I:%M %p')}."
        )
    )
    db.session.add(message)

    send_notification(
        resource.owner,
        title=f"Action needed: {resource.title}",
        message=(
            f"{requester.name} requested a booking for {resource.title}. "
            "Please review and approve or reject the request."
        ),
        notification_type="owner_action_required",
        related_url=url_for("resource_bp.owner_requests")
    )

    return booking_request

