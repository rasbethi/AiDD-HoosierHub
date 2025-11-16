from flask import Blueprint, render_template, Response, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import timezone, datetime

from src.models.models import db, Booking, Waitlist
from src.data_access import bookings_dal, waitlist_dal
from src.services.booking_rules import validate_time_block
from src.services.waitlist_service import promote_waitlist_entry

booking_bp = Blueprint("booking", __name__, url_prefix="/bookings")


@booking_bp.route("/")
@login_required
def dashboard():
    if current_user.is_authenticated and current_user.is_admin():
        bookings = bookings_dal.list_all_bookings()
        view_mode = "all"
        waitlist_entries = []
    else:
        bookings = bookings_dal.list_bookings_for_user(current_user.id)
        view_mode = "personal"
        waitlist_entries = waitlist_dal.list_waiting_entries_for_user(current_user.id)

        # Auto-promote any waitlist entries that now have capacity
        conversions = []
        for entry in list(waitlist_entries):
            if not entry.start_time or not entry.end_time:
                continue
            booking = promote_waitlist_entry(entry.resource, entry.start_time, entry.end_time)
            if booking:
                conversions.append(entry.id)

        if conversions:
            db.session.commit()
            flash("A slot opened and we booked it automatically. Check your bookings for details.", "info")
            bookings = bookings_dal.list_bookings_for_user(current_user.id)
            waitlist_entries = waitlist_dal.list_waiting_entries_for_user(current_user.id)

    return render_template(
        "bookings/dashboard.html",
        bookings=bookings,
        view_mode=view_mode,
        waitlist_entries=waitlist_entries
    )


@booking_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_my_booking(booking_id):
    booking = bookings_dal.get_booking_or_404(booking_id)
    if booking.user_id != current_user.id and not current_user.is_admin():
        abort(403)

    if booking.status == "cancelled":
        flash("This booking is already cancelled.", "info")
        return redirect(request.form.get("return_to") or url_for("booking.dashboard"))

    resource = booking.resource
    slot_start = booking.start_time
    slot_end = booking.end_time

    booking.status = "cancelled"
    booking.decision_at = datetime.now(timezone.utc)
    booking.rejection_reason = "Cancelled by user"

    if hasattr(booking, "request") and booking.request:
        booking.request.mark("closed", "Cancelled by requester.")

    db.session.flush()
    promoted_booking = promote_waitlist_entry(resource, slot_start, slot_end)
    db.session.commit()

    flash("Booking cancelled.", "success")
    if promoted_booking:
        flash("Someone on the waitlist was auto-booked for this slot.", "info")

    return redirect(request.form.get("return_to") or url_for("booking.dashboard"))


@booking_bp.route("/<int:booking_id>")
@login_required
def detail(booking_id):
    """Show detailed view of a single booking for the current user."""
    booking = bookings_dal.get_booking_or_404(booking_id)

    if not current_user.is_admin() and booking.user_id != current_user.id and booking.resource.owner_id != current_user.id:
        abort(403)

    owner_can_manage = (booking.resource.owner_id == current_user.id) or current_user.is_admin()
    can_cancel = (booking.user_id == current_user.id) and booking.status not in ("cancelled", "rejected")

    return render_template(
        "bookings/detail.html",
        booking=booking,
        owner_can_manage=owner_can_manage,
        can_cancel=can_cancel
    )


@booking_bp.route("/waitlist/<int:entry_id>", methods=["GET", "POST"])
@login_required
def waitlist_detail(entry_id):
    entry = waitlist_dal.get_waitlist_entry_or_404(entry_id)

    permitted = (
        current_user.is_admin()
        or entry.user_id == current_user.id
        or entry.resource.owner_id == current_user.id
    )
    if not permitted:
        abort(403)

    can_edit = current_user.is_admin() or entry.user_id == current_user.id

    if request.method == "POST":
        if not can_edit:
            abort(403)

        start_raw = request.form.get("start_time")
        end_raw = request.form.get("end_time")
        purpose = (request.form.get("purpose") or "").strip()

        try:
            start_dt = datetime.fromisoformat(start_raw) if start_raw else None
            end_dt = datetime.fromisoformat(end_raw) if end_raw else None
        except ValueError:
            flash("Please provide valid start and end times (e.g., 7:00 PM – 8:00 PM).", "warning")
            return redirect(url_for("booking.waitlist_detail", entry_id=entry.id))

        if not start_dt or not end_dt:
            flash("Waitlist entries need both start and end times.", "warning")
            return redirect(url_for("booking.waitlist_detail", entry_id=entry.id))

        try:
            validate_time_block(start_dt, end_dt)
        except ValueError as exc:
            flash(str(exc), "warning")
            return redirect(url_for("booking.waitlist_detail", entry_id=entry.id))

        entry.start_time = start_dt
        entry.end_time = end_dt
        entry.purpose = purpose or entry.purpose
        entry.status = entry.status or "waiting"
        db.session.commit()
        flash("Waitlist slot updated.", "success")
        return redirect(url_for("booking.waitlist_detail", entry_id=entry.id))

    return render_template("bookings/waitlist_detail.html", entry=entry, can_edit=can_edit)


def _format_ics_datetime(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


@booking_bp.route("/export.ics")
@login_required
def export_ics():
    """Generate an iCal feed of the user's bookings."""
    if current_user.is_admin():
        bookings = Booking.query.order_by(Booking.start_time.asc()).all()
    else:
        bookings = (
            Booking.query
            .filter_by(user_id=current_user.id)
            .order_by(Booking.start_time.asc())
            .all()
        )

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Hoosier Hub//EN",
        "CALSCALE:GREGORIAN",
    ]

    for booking in bookings:
        resource = booking.resource
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:booking-{booking.id}@campushub",
            f"DTSTAMP:{_format_ics_datetime(booking.created_at or booking.start_time)}",
            f"DTSTART:{_format_ics_datetime(booking.start_time)}",
            f"DTEND:{_format_ics_datetime(booking.end_time)}",
            f"SUMMARY:{resource.title}",
            f"LOCATION:{resource.location or 'Hoosier Hub Resource'}",
            f"DESCRIPTION:Reserved for {booking.user.name} (Status: {booking.status})",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(lines)
    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=campus-resource-bookings.ics"
        }
    )
