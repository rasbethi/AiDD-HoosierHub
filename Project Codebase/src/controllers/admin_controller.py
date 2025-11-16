from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta, timezone

from src.models.models import (
    db,
    User,
    Resource,
    Booking,
    Review,
    EmailLog,
    Waitlist,
    BookingRequest,
    Message,
    DowntimeBlock,
    Notification,
    SitePage,
)
from src.data_access import resources_dal, bookings_dal, waitlist_dal
from sqlalchemy import func
from src.services.notification_service import send_notification
from src.services.booking_service import create_owner_booking_request
from src.services.booking_rules import validate_time_block, ensure_capacity
from src.services.slot_service import build_slot_days
from src.services.waitlist_service import promote_waitlist_entry
from src.utils.db_helpers import get_or_404

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# Admin Required Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Admin access required!", "danger")
            return redirect(url_for("resource_bp.list_resources"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
@admin_required
def mark_notification_read(notification_id):
    note = get_or_404(Notification, notification_id)
    if note.user_id != current_user.id:
        abort(403)
    note.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/pages", methods=["GET", "POST"])
@login_required
@admin_required
def manage_pages():
    allowed_slugs = {"about", "contact"}
    if request.method == "POST":
        slug = request.form.get("slug")
        if slug not in allowed_slugs:
            abort(400)
        page = SitePage.query.filter_by(slug=slug).first_or_404()
        page.title = request.form.get("title", page.title)
        page.body = request.form.get("body", page.body)
        page.updated_by = current_user.id
        db.session.commit()
        flash(f"{page.title} updated successfully.", "success")
        return redirect(url_for("admin.manage_pages"))

    pages = (
        SitePage.query
        .filter(SitePage.slug.in_(allowed_slugs))
        .order_by(SitePage.slug)
        .all()
    )
    return render_template("admin/pages.html", pages=pages)


# --------------------------
# ADMIN DASHBOARD
# --------------------------
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview stats."""
    
    # Get statistics
    total_users = User.query.count()
    total_resources = Resource.query.count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status="pending").count()
    now_utc = datetime.now(timezone.utc)
    sla_threshold = now_utc - timedelta(hours=24)
    overdue_bookings = (
        Booking.query
        .filter(
            Booking.status == "pending",
            Booking.created_at <= sla_threshold
        )
        .order_by(Booking.created_at.asc())
        .all()
    )

    decided_bookings = (
        Booking.query
        .filter(Booking.decision_at.isnot(None))
        .all()
    )
    if decided_bookings:
        avg_response_seconds = sum(
            max((booking.decision_at - booking.created_at).total_seconds(), 0)
            for booking in decided_bookings
        ) / len(decided_bookings)
        avg_response_hours = round(avg_response_seconds / 3600, 2)
    else:
        avg_response_hours = None

    utilization_start = now_utc - timedelta(days=7)
    utilization_bookings = (
        Booking.query
        .filter(
            Booking.status == "approved",
            Booking.start_time >= utilization_start,
            Booking.start_time <= now_utc
        )
        .all()
    )

    utilization_map = {}
    hours_window = 7 * 24
    for booking in utilization_bookings:
        duration_hours = max((booking.end_time - booking.start_time).total_seconds() / 3600, 0)
        entry = utilization_map.setdefault(booking.resource_id, {
            "resource": booking.resource,
            "hours": 0.0,
            "count": 0
        })
        entry["hours"] += duration_hours
        entry["count"] += 1

    utilization_stats = []
    for resource_id, data in utilization_map.items():
        resource = data["resource"]
        capacity = max(resource.capacity or 1, 1)
        seat_hours_available = capacity * hours_window
        utilization_pct = min((data["hours"] / seat_hours_available) * 100 if seat_hours_available else 0, 100)
        utilization_stats.append({
            "resource": resource,
            "hours": round(data["hours"], 2),
            "count": data["count"],
            "utilization_pct": round(utilization_pct, 1)
        })

    utilization_stats.sort(key=lambda item: item["utilization_pct"], reverse=True)
    top_utilization = utilization_stats[:5]
    
    # Recent activity
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_resources = Resource.query.order_by(Resource.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    # Role & department analytics
    role_usage = (
        db.session.query(User.role, func.count(Booking.id))
        .join(Booking, Booking.user_id == User.id)
        .group_by(User.role)
        .all()
    )

    resource_type_usage = (
        db.session.query(Resource.category, func.count(Booking.id))
        .join(Booking, Booking.resource_id == Resource.id)
        .group_by(Resource.category)
        .order_by(func.count(Booking.id).desc())
        .limit(6)
        .all()
    )

    department_usage = (
        db.session.query(User.department, func.count(Booking.id))
        .join(Booking, Booking.user_id == User.id)
        .group_by(User.department)
        .order_by(func.count(Booking.id).desc())
        .limit(6)
        .all()
    )

    summary_window_start = now_utc - timedelta(days=7)
    summary_bookings = (
        db.session.query(Resource.title, func.count(Booking.id).label("total"))
        .join(Resource, Booking.resource_id == Resource.id)
        .filter(
            Booking.start_time >= summary_window_start,
            Booking.status.in_(["approved", "pending"]),
        )
        .group_by(Resource.id)
        .order_by(func.count(Booking.id).desc())
        .limit(5)
        .all()
    )
    weekly_summary = [
        {"title": title, "count": total} for title, total in summary_bookings
    ]
    
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_resources=total_resources,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        overdue_bookings=overdue_bookings,
        avg_response_hours=avg_response_hours,
        top_utilization=top_utilization,
        utilization_window_start=utilization_start,
        recent_bookings=recent_bookings,
        recent_resources=recent_resources,
        recent_users=recent_users,
        role_usage=role_usage,
        resource_type_usage=resource_type_usage,
        department_usage=department_usage,
        weekly_summary=weekly_summary,
        summary_window_start=summary_window_start,
    )


# --------------------------
# MANAGE RESOURCES
# --------------------------
@admin_bp.route("/resources")
@login_required
@admin_required
def manage_resources():
    """View and manage all resources."""
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return render_template("admin/resources.html", resources=resources)


@admin_bp.route("/resources/<int:resource_id>/status", methods=["POST"])
@login_required
@admin_required
def update_resource_status(resource_id):
    """Update lifecycle status for a resource."""
    resource = resources_dal.get_resource_or_404(resource_id)
    new_status = request.form.get("status")

    valid_statuses = {
        Resource.STATUS_DRAFT,
        Resource.STATUS_PUBLISHED,
        Resource.STATUS_ARCHIVED,
    }

    if new_status not in valid_statuses:
        flash("Invalid status value.", "danger")
        return redirect(url_for("admin.manage_resources"))

    resource.status = new_status
    resource.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash(f"Resource '{resource.title}' status updated to {new_status}.", "success")
    return redirect(url_for("admin.manage_resources"))


# --------------------------
# MANAGE REVIEWS
# --------------------------
@admin_bp.route("/reviews")
@login_required
@admin_required
def manage_reviews():
    """View and manage all reviews."""
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=reviews)


@admin_bp.route("/reviews/delete/<int:review_id>", methods=["POST"])
@login_required
@admin_required
def delete_review(review_id):
    """Admin delete any review."""
    review = get_or_404(Review, review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted successfully!", "success")
    return redirect(url_for("admin.manage_reviews"))


# --------------------------
# BOOKING REQUESTS INBOX
# --------------------------
@admin_bp.route("/requests")
@login_required
@admin_required
def list_requests():
    """List booking requests that need admin attention."""
    status_filter = request.args.get("status")
    resource_filter = request.args.get("resource_id", type=int)

    ordering = db.case(
        (BookingRequest.status == "pending", 0),
        (BookingRequest.status == "approved", 1),
        (BookingRequest.status == "denied", 2),
        else_=3
    )

    query = (
        BookingRequest.query
        .filter(BookingRequest.kind == "allocator")
        .order_by(ordering, BookingRequest.created_at.desc())
    )

    valid_statuses = ["pending", "approved", "denied", "closed"]
    if status_filter in valid_statuses:
        query = query.filter(BookingRequest.status == status_filter)
    else:
        status_filter = None

    if resource_filter:
        query = query.filter(BookingRequest.resource_id == resource_filter)

    requests = query.all()
    resource_options = Resource.query.order_by(Resource.title.asc()).all()

    return render_template(
        "admin/requests.html",
        requests=requests,
        status_filter=status_filter,
        resource_filter=resource_filter,
        resource_options=resource_options,
        valid_statuses=valid_statuses
    )


@admin_bp.route("/inbox")
@login_required
@admin_required
def admin_inbox():
    """Admin inbox showing only 'book for me' requests."""
    status_filter = request.args.get("status")

    ordering = db.case(
        (BookingRequest.status == "pending", 0),
        (BookingRequest.status == "approved", 1),
        (BookingRequest.status == "denied", 2),
        else_=3
    )

    query = (
        BookingRequest.query
        .filter(BookingRequest.kind == "allocator")
        .order_by(ordering, BookingRequest.created_at.desc())
    )

    valid_statuses = ["pending", "approved", "denied", "closed"]
    if status_filter in valid_statuses:
        query = query.filter(BookingRequest.status == status_filter)
    else:
        status_filter = None

    requests = query.limit(200).all()

    return render_template(
        "admin/inbox.html",
        requests=requests,
        status_filter=status_filter,
        valid_statuses=valid_statuses
    )


@admin_bp.route("/email-log")
@login_required
@admin_required
def email_log():
    """View simulated email notifications."""
    logs = (
        EmailLog.query
        .order_by(EmailLog.sent_at.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/email_log.html", logs=logs)


@admin_bp.route("/requests/<int:request_id>")
@login_required
@admin_required
def view_request(request_id):
    """Detail view for a specific booking request."""
    booking_request = get_or_404(BookingRequest, request_id)
    messages = (
        Message.query
        .filter_by(request_id=request_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return render_template(
        "admin/request_detail.html",
        booking_request=booking_request,
        messages=messages
    )


@admin_bp.route("/requests/<int:request_id>/decision", methods=["POST"])
@login_required
@admin_required
def decide_request(request_id):
    """Approve, deny, or close a booking request."""
    booking_request = get_or_404(BookingRequest, request_id)
    if booking_request.kind != "allocator":
        flash("Owner approvals must be handled in the Owner Inbox.", "warning")
        return redirect(url_for("admin.admin_inbox"))

    action = request.form.get("action")
    note = request.form.get("note", "").strip()

    if action not in {"deny", "close", "reopen"}:
        flash("Unsupported action.", "danger")
        return redirect(url_for("admin.view_request", request_id=request_id))

    if action == "deny":
        booking_request.mark("denied", note or "Request denied by admin.")
        booking_request.booking_id = None

        denial_message = Message(
            sender_id=current_user.id,
            receiver_id=booking_request.requester_id,
            request_id=booking_request.id,
            subject="Booking request denied",
            content=note or "This booking request was denied by the admin team."
        )
        db.session.add(denial_message)

        send_notification(
            booking_request.requester,
            title="Booking Request Denied",
            message=f"Your request for {booking_request.resource.title} was denied.",
            notification_type="booking_request_denied",
            related_url=url_for("resource_bp.resource_detail", resource_id=booking_request.resource_id),
        )
        flash("Request denied.", "warning")

    elif action == "close":
        booking_request.mark("closed", note or "Request closed.")
        flash("Request closed.", "info")

    elif action == "reopen":
        booking_request.status = "pending"
        booking_request.decision_note = None
        booking_request.decided_at = None
        flash("Request reopened and moved back to the pending queue.", "success")

    db.session.commit()
    return redirect(url_for("admin.view_request", request_id=request_id))


# --------------------------
# BOOK RESOURCE FOR USER (ADMIN ONLY)
# --------------------------
@admin_bp.route("/book-for-user", methods=["GET", "POST"])
@login_required
@admin_required
def book_for_user():
    """Admin can book resources for any user."""
    return_to = request.args.get("return_to") or request.form.get("return_to", "")
    selected_resource_id = request.args.get("resource_id", type=int) or request.form.get("resource_id", type=int)
    request_id = request.args.get("request_id", type=int) or request.form.get("request_id", type=int)
    
    if request.method == "POST" and request.form.get("booking_action") == "create":
        resource_id = request.form.get("resource_id", type=int)
        user_id = request.form.get("user_id", type=int)
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        purpose = request.form.get("purpose")
        request_id = request.form.get("request_id", type=int)
        
        resource = resources_dal.get_resource_or_404(resource_id)
        user = get_or_404(User, user_id)
        linked_request = db.session.get(BookingRequest, request_id) if request_id else None

        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except (TypeError, ValueError):
            flash("Invalid date format. Please use the provided pickers.", "danger")
            return redirect(
                url_for(
                    "admin.book_for_user",
                    resource_id=resource_id,
                    return_to=return_to,
                    request_id=request_id,
                    start_time=start_time,
                    end_time=end_time,
                    user_id=user_id,
                    purpose=purpose,
                )
            )

        try:
            validate_time_block(start_dt, end_dt)
        except ValueError as exc:
            flash(str(exc), "warning")
            return redirect(
                url_for(
                    "admin.book_for_user",
                    resource_id=resource_id,
                    return_to=return_to,
                    request_id=request_id,
                    start_time=start_time,
                    end_time=end_time,
                    user_id=user_id,
                    purpose=purpose,
                )
            )

        recurrence = request.form.get("recurrence", "none")
        recurrence_count = request.form.get("recurrence_count", type=int) or 1
        recurrence_count = max(1, min(recurrence_count, 10))

        delta_lookup = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
        }

        occurrences = [(start_dt, end_dt)]
        if recurrence in delta_lookup and recurrence_count > 1:
            delta = delta_lookup[recurrence]
            for i in range(1, recurrence_count):
                occ_start = start_dt + i * delta
                occ_end = end_dt + i * delta
                occurrences.append((occ_start, occ_end))

        for occ_start, occ_end in occurrences:
            downtime = (
                DowntimeBlock.query
                .filter_by(resource_id=resource_id)
                .filter(
                    DowntimeBlock.start_time < occ_end,
                    DowntimeBlock.end_time > occ_start
                )
                .first()
            )

            if downtime:
                flash(
                    f"This resource is unavailable between "
                    f"{downtime.start_time.strftime('%b %d, %Y %I:%M %p')} and "
                    f"{downtime.end_time.strftime('%b %d, %Y %I:%M %p')} (reason: {downtime.reason or 'maintenance'}).",
                    "warning"
                )
                return redirect(
                    url_for(
                        "admin.book_for_user",
                        resource_id=resource_id,
                        return_to=return_to,
                        request_id=request_id,
                        start_time=start_time,
                        end_time=end_time,
                        user_id=user_id,
                        purpose=purpose,
                    )
                )

            try:
                ensure_capacity(resource, occ_start, occ_end)
            except ValueError as exc:
                flash(str(exc), "warning")
                query_params = dict(
                    resource_id=resource_id,
                    return_to=return_to,
                    waitlist="1",
                    user_id=user_id,
                    start_time=start_time,
                    end_time=end_time,
                    purpose=purpose,
                    request_id=request_id,
                )
                return redirect(url_for("admin.book_for_user", **query_params))

        auto_approve = resource.access_type == "public"

        created_bookings = []
        for occ_start, occ_end in occurrences:
            booking_record = Booking(
            resource_id=resource_id,
            user_id=user_id,
                start_time=occ_start,
                end_time=occ_end,
            purpose=purpose or f"Booked by admin for {user.name}",
                booked_by_admin=True,
                status="approved" if auto_approve else "pending",
                approved_by=current_user.id if auto_approve else None,
                decision_at=datetime.now(timezone.utc) if auto_approve else None
            )
            db.session.add(booking_record)
            db.session.flush()

            if not auto_approve:
                requester_context = linked_request.requester if linked_request else user
                create_owner_booking_request(resource, booking_record, requester_context, purpose)

            created_bookings.append(booking_record)

        # If this booking originated from a request, update it
        if linked_request:
            linked_request.booking_id = created_bookings[0].id
            if auto_approve:
                linked_request.mark("approved", purpose or "Approved by admin.")

                approval_message = Message(
                    sender_id=current_user.id,
                    receiver_id=linked_request.requester_id,
                    request_id=linked_request.id,
                    subject="Booking request approved",
                    content=(
                        f"Your booking request for {resource.title} was approved. "
                        f"Scheduled from {start_dt.strftime('%b %d %I:%M %p')} to {end_dt.strftime('%b %d %I:%M %p')}."
                    )
                )
                db.session.add(approval_message)

                send_notification(
                    linked_request.requester,
                    title="Booking Request Approved",
                    message=f"An admin booked {resource.title} on your behalf.",
                    notification_type="booking_request_approved",
                    related_url=url_for("resource_bp.resource_detail", resource_id=resource_id),
                )
            else:
                linked_request.status = "pending"
                linked_request.decision_note = None
                linked_request.decided_at = None

                pending_message = Message(
                    sender_id=current_user.id,
                    receiver_id=linked_request.requester_id,
                    request_id=linked_request.id,
                    subject="Booking request in review",
                    content=(
                        f"We scheduled {resource.title} for you, but the resource owner must approve it. "
                        "We'll let you know once they decide."
                    )
                )
                db.session.add(pending_message)

                send_notification(
                    linked_request.requester,
                    title="Booking request pending owner approval",
                    message=f"{resource.title} is scheduled, but the owner still needs to approve it.",
                    notification_type="booking_pending",
                    related_url=url_for("booking.dashboard"),
                )
        
        # Send notification to user
        notif_message = f"Admin has booked {resource.title} for you from {start_time} to {end_time}"
        if not auto_approve:
            notif_message += ". The booking is pending approval."
        if len(created_bookings) > 1:
            notif_message += f" ({len(created_bookings)} total occurrences)."

        if not request_id:
            send_notification(
                user,
            title="Booking Confirmed",
                message=notif_message,
                notification_type="booking_approved" if auto_approve else "booking_pending",
                related_url="/bookings",
        )
        
        db.session.commit()
        
        if auto_approve:
            flash(f"Successfully booked {resource.title} for {user.name}! ({len(created_bookings)} occurrence{'s' if len(created_bookings) > 1 else ''})", "success")
        else:
            flash(f"Booking request for {resource.title} was submitted and is awaiting approval.", "info")

        if return_to:
            return redirect(return_to)
        return redirect(url_for("admin.book_for_user"))
    
    elif request.method == "POST" and request.form.get("waitlist_action") == "add":
        user_id = request.form.get("user_id", type=int)
        resource_id = request.form.get("resource_id", type=int) or selected_resource_id
        start_time_raw = request.form.get("start_time")
        end_time_raw = request.form.get("end_time")
        purpose = (request.form.get("purpose") or "").strip()

        if not user_id or not resource_id:
            flash("Select a user and resource before adding to the waitlist.", "warning")
            return redirect(
                url_for(
                    "admin.book_for_user",
                    resource_id=resource_id,
                    return_to=return_to,
                    waitlist="1",
                    user_id=user_id,
                    start_time=start_time_raw,
                    end_time=end_time_raw,
                    purpose=purpose,
                )
            )

        resource = resources_dal.get_resource_or_404(resource_id)
        user = get_or_404(User, user_id)

        try:
            start_dt = datetime.fromisoformat(start_time_raw) if start_time_raw else None
            end_dt = datetime.fromisoformat(end_time_raw) if end_time_raw else None
        except ValueError:
            flash("Provide a valid start and end time for the waitlist entry.", "warning")
            return redirect(
                url_for(
                    "admin.book_for_user",
                    resource_id=resource_id,
                    return_to=return_to,
                    waitlist="1",
                    user_id=user_id,
                    start_time=start_time_raw,
                    end_time=end_time_raw,
                    purpose=purpose,
                )
            )

        if not start_dt or not end_dt:
            flash("Please select a start and end time before adding to the waitlist.", "warning")
            return redirect(
                url_for(
                    "admin.book_for_user",
                    resource_id=resource_id,
                    return_to=return_to,
                    waitlist="1",
                    user_id=user_id,
                    start_time=start_time_raw,
                    end_time=end_time_raw,
                    purpose=purpose,
                )
            )

        try:
            validate_time_block(start_dt, end_dt)
        except ValueError as exc:
            flash(str(exc), "warning")
            return redirect(
                url_for(
                    "admin.book_for_user",
                    resource_id=resource_id,
                    return_to=return_to,
                    waitlist="1",
                    user_id=user_id,
                    start_time=start_time_raw,
                    end_time=end_time_raw,
                    purpose=purpose,
                )
            )

        existing = Waitlist.query.filter_by(
            resource_id=resource.id,
            user_id=user.id
        ).first()

        if existing:
            flash(f"{user.name} is already on the waitlist for {resource.title}.", "info")
        else:
            max_position = db.session.query(db.func.max(Waitlist.position)).filter_by(
                resource_id=resource.id
            ).scalar() or 0

            waitlist_entry = Waitlist(
                resource_id=resource.id,
                user_id=user.id,
                position=max_position + 1,
                start_time=start_dt,
                end_time=end_dt,
                purpose=purpose,
                status="waiting",
            )
            db.session.add(waitlist_entry)
            db.session.commit()
            flash(f"Added {user.name} to the waitlist for {resource.title}.", "success")

        if return_to:
            return redirect(return_to)
        return redirect(
            url_for(
                "admin.book_for_user",
                resource_id=resource_id,
                waitlist="1",
                user_id=user_id,
                start_time=start_time_raw,
                end_time=end_time_raw,
                purpose=purpose,
            )
        )
    
    # GET request - show form
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    users = (
        User.query
        .filter(User.role.in_(["student", "staff"]), User.status == "active")
        .order_by(User.name.asc())
        .all()
    )
    slot_days = []
    if selected_resource_id:
        selected_resource = db.session.get(Resource, selected_resource_id)
        if selected_resource:
            slot_days = build_slot_days(selected_resource)
    
    return render_template(
        "admin/book_for_user.html",
        resources=resources,
        users=users,
        selected_resource_id=selected_resource_id,
        return_to=return_to,
        request_id=request_id,
        slot_days=slot_days
    )


# --------------------------
# MANAGE USERS
# --------------------------
@admin_bp.route("/users")
@login_required
@admin_required
def manage_users():
    """View and manage all users."""
    users = (
        User.query
        .order_by(User.status.asc(), User.created_at.desc())
        .all()
    )
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    """Admin delete user."""
    if user_id == current_user.id:
        flash("You cannot delete yourself!", "danger")
        return redirect(url_for("admin.manage_users"))
    
    user = get_or_404(User, user_id)
    name = user.name
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{name}' deleted successfully!", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/status/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def update_user_status(user_id):
    """Activate or deactivate a user without changing their role."""
    if user_id == current_user.id:
        flash("You cannot change your own status!", "danger")
        return redirect(url_for("admin.manage_users"))

    user = get_or_404(User, user_id)
    new_status = request.form.get("status")
    
    if new_status not in ["active", "inactive"]:
        flash("Invalid status value.", "danger")
        return redirect(url_for("admin.manage_users"))

    if user.status == new_status:
        flash(f"{user.name} is already {new_status}.", "info")
        return redirect(url_for("admin.manage_users"))

    user.status = new_status
    db.session.commit()

    if new_status == "active":
        flash(f"{user.name} has been reactivated.", "success")
    else:
        flash(f"{user.name} has been set to inactive.", "warning")
    
    return redirect(url_for("admin.manage_users"))


# --------------------------
# MANAGE BOOKINGS
# --------------------------
@admin_bp.route("/bookings")
@login_required
@admin_required
def manage_bookings():
    """View all bookings."""
    bookings = Booking.query.order_by(Booking.start_time.desc()).all()
    return render_template("admin/bookings.html", bookings=bookings)


@admin_bp.route("/bookings/approve/<int:booking_id>", methods=["POST"])
@login_required
@admin_required
def approve_booking(booking_id):
    """Admin approve booking."""
    booking = bookings_dal.get_booking_or_404(booking_id)
    if booking.resource.access_type == "restricted":
        flash("Restricted resources must be approved by their owner via the Owner Inbox.", "warning")
        return redirect(request.referrer or url_for("admin.manage_bookings"))
    booking.status = "approved"
    booking.approved_by = current_user.id
    booking.decision_at = datetime.now(timezone.utc)
    
    send_notification(
        booking.user,
        title="Booking Approved",
        message=f"Your booking for {booking.resource.title} has been approved!",
        notification_type="booking_approved",
        related_url="/bookings",
    )
    db.session.commit()
    
    flash("Booking approved!", "success")
    return redirect(url_for("admin.manage_bookings"))


@admin_bp.route("/bookings/reject/<int:booking_id>", methods=["POST"])
@login_required
@admin_required
def reject_booking(booking_id):
    """Admin reject booking."""
    booking = bookings_dal.get_booking_or_404(booking_id)
    resource = booking.resource
    slot_start = booking.start_time
    slot_end = booking.end_time
    reason = (request.form.get("reason") or "").strip()
    redirect_target = request.referrer or url_for("admin.manage_bookings")

    if booking.resource.access_type == "restricted" and booking.resource.owner_id != current_user.id:
        booking.status = "rejected"
        booking.rejection_reason = reason or "Cancelled by admin on behalf of owner"
        booking.decision_at = datetime.now(timezone.utc)
        booking.deleted_by_admin = True
        notify_message = (
            f"Your booking for {booking.resource.title} was cancelled by the admin: {booking.rejection_reason}"
        )
        notify_title = "Booking Cancelled"
        flash_copy = ("Booking cancelled and the user has been notified.", "success")
    else:
        booking.status = "rejected"
        booking.rejection_reason = reason or "Rejected by admin"
        booking.decision_at = datetime.now(timezone.utc)
        notify_message = (
            f"Your booking for {booking.resource.title} was rejected: {booking.rejection_reason}"
        )
        notify_title = "Booking Rejected"
        flash_copy = ("Booking rejected!", "success")

    send_notification(
        booking.user,
        title=notify_title,
        message=notify_message,
        notification_type="booking_rejected",
        related_url="/bookings",
    )

    db.session.flush()
    promoted_booking = promote_waitlist_entry(resource, slot_start, slot_end, actor=current_user)
    db.session.commit()

    flash(*flash_copy)
    if promoted_booking:
        flash("Next person on the waitlist was auto-booked for this slot.", "info")
    return redirect(redirect_target)


@admin_bp.route("/bookings/cancel/<int:booking_id>", methods=["POST"])
@login_required
@admin_required
def cancel_booking(booking_id):
    """Admin manually cancels a booking."""
    booking = bookings_dal.get_booking_or_404(booking_id)
    resource = booking.resource
    slot_start = booking.start_time
    slot_end = booking.end_time
    reason = (request.form.get("reason") or "").strip()
    redirect_target = request.referrer or url_for("admin.manage_bookings")

    booking.status = "cancelled"
    booking.rejection_reason = reason or "Cancelled by admin"
    booking.decision_at = datetime.now(timezone.utc)

    send_notification(
        booking.user,
        title="Booking Cancelled",
        message=(
            f"Your booking for {booking.resource.title} was cancelled."
            + (f" Reason: {booking.rejection_reason}" if booking.rejection_reason else "")
        ),
        notification_type="booking_cancelled",
        related_url="/bookings",
    )

    db.session.flush()
    promoted_booking = promote_waitlist_entry(resource, slot_start, slot_end, actor=current_user)
    db.session.commit()
    
    flash("Booking cancelled and the user has been notified.", "success")
    if promoted_booking:
        flash("Next person on the waitlist was auto-booked for this slot.", "info")
    return redirect(redirect_target)


@admin_bp.route("/bookings/delete/<int:booking_id>", methods=["POST"])
@login_required
@admin_required
def delete_booking(booking_id):
    """Admin delete booking."""
    booking = bookings_dal.get_booking_or_404(booking_id)
    resource = booking.resource
    slot_start = booking.start_time
    slot_end = booking.end_time

    db.session.delete(booking)
    db.session.flush()
    promoted_booking = promote_waitlist_entry(resource, slot_start, slot_end, actor=current_user)
    db.session.commit()

    flash("Booking deleted!", "success")
    if promoted_booking:
        flash("Next person on the waitlist was auto-booked for this slot.", "info")
    return redirect(request.referrer or url_for("admin.manage_bookings"))


@admin_bp.route("/bookings/<int:booking_id>")
@login_required
@admin_required
def view_booking(booking_id):
    """Detailed view for a single booking."""
    booking = bookings_dal.get_booking_or_404(booking_id)
    return render_template("admin/booking_detail.html", booking=booking)


@admin_bp.route("/resources/<int:resource_id>/schedule")
@login_required
@admin_required
def resource_schedule(resource_id):
    """Show schedule/calendar for a specific resource."""
    resource = resources_dal.get_resource_or_404(resource_id)
    bookings = (
        Booking.query
        .filter_by(resource_id=resource_id)
        .order_by(Booking.start_time.asc())
        .all()
    )
    users = User.query.filter(User.role.in_(["student", "staff"])).order_by(User.name.asc()).all()
    waitlist_entries = (
        Waitlist.query
        .filter_by(resource_id=resource_id)
        .order_by(Waitlist.position.asc(), Waitlist.created_at.asc())
        .all()
    )
    downtimes = (
        DowntimeBlock.query
        .filter_by(resource_id=resource_id)
        .order_by(DowntimeBlock.start_time.asc())
        .all()
    )

    return render_template(
        "admin/resource_schedule.html",
        resource=resource,
        bookings=bookings,
        users=users,
        waitlist_entries=waitlist_entries,
        downtimes=downtimes
    )


@admin_bp.route("/waitlist/<int:entry_id>/remove", methods=["POST"])
@login_required
@admin_required
def remove_waitlist_entry(entry_id):
    entry = waitlist_dal.get_waitlist_entry_or_404(entry_id)
    resource_id = entry.resource_id
    db.session.delete(entry)
    db.session.commit()
    flash("Removed from waitlist.", "success")

    return_to = request.form.get("return_to")
    if return_to:
        return redirect(return_to)
    return redirect(url_for("admin.resource_schedule", resource_id=resource_id))


@admin_bp.route("/resources/<int:resource_id>/downtime", methods=["POST"])
@login_required
@admin_required
def create_downtime_block(resource_id):
    resource = resources_dal.get_resource_or_404(resource_id)
    start_raw = request.form.get("downtime_start")
    end_raw = request.form.get("downtime_end")
    reason = request.form.get("downtime_reason", "").strip()

    if not start_raw or not end_raw:
        flash("Please provide both a start and end time for the downtime block.", "warning")
        return redirect(url_for("admin.resource_schedule", resource_id=resource_id))

    try:
        start_time = datetime.fromisoformat(start_raw)
        end_time = datetime.fromisoformat(end_raw)
    except ValueError:
        flash("Invalid datetime format for downtime block.", "danger")
        return redirect(url_for("admin.resource_schedule", resource_id=resource_id))

    if start_time >= end_time:
        flash("Downtime end must be after start.", "warning")
        return redirect(url_for("admin.resource_schedule", resource_id=resource_id))

    block = DowntimeBlock(
        resource_id=resource_id,
        created_by=current_user.id,
        start_time=start_time,
        end_time=end_time,
        reason=reason or "Scheduled downtime"
    )
    db.session.add(block)
    db.session.flush()

    impacted_bookings = (
        Booking.query
        .filter(
            Booking.resource_id == resource_id,
            Booking.status.in_(["pending", "approved"]),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )
        .all()
    )

    cancellation_reason = (
        f"Booking cancelled due to downtime from "
        f"{start_time.strftime('%b %d, %Y %I:%M %p')} to "
        f"{end_time.strftime('%b %d, %Y %I:%M %p')}."
    )

    for booking in impacted_bookings:
        booking.status = "cancelled"
        booking.decision_at = datetime.now(timezone.utc)
        booking.rejection_reason = cancellation_reason

        send_notification(
            booking.user,
            title="Booking Cancelled",
            message=cancellation_reason,
            notification_type="booking_cancelled",
            related_url=url_for("booking.dashboard"),
        )

        if hasattr(booking, "request") and booking.request:
            message = Message(
                sender_id=current_user.id,
                receiver_id=booking.user_id,
                request_id=booking.request.id,
                subject="Booking cancelled",
                content=cancellation_reason
            )
            db.session.add(message)

    db.session.commit()

    flash(
        f"Downtime created from {start_time.strftime('%b %d %I:%M %p')} to {end_time.strftime('%I:%M %p')}. "
        f"Impacted bookings: {len(impacted_bookings)}.",
        "success"
    )
    return redirect(url_for("admin.resource_schedule", resource_id=resource_id))


@admin_bp.route("/downtime/<int:block_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_downtime_block(block_id):
    block = get_or_404(DowntimeBlock, block_id)
    resource_id = block.resource_id
    db.session.delete(block)
    db.session.commit()
    flash("Downtime block removed.", "info")
    return_to = request.form.get("return_to")
    if return_to:
        return redirect(return_to)
    return redirect(url_for("admin.resource_schedule", resource_id=resource_id))


@admin_bp.route("/bookings/<int:booking_id>/reschedule", methods=["POST"])
@login_required
@admin_required
def reschedule_booking(booking_id):
    """Ajax endpoint to reschedule a booking via drag-and-drop UI."""
    booking = bookings_dal.get_booking_or_404(booking_id)
    data = request.get_json() or {}

    new_start_raw = data.get("start_time")
    new_resource_id = data.get("resource_id", booking.resource_id)

    if not new_start_raw:
        return jsonify({"success": False, "message": "Missing start time."}), 400

    try:
        new_start = datetime.fromisoformat(new_start_raw)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid start time format."}), 400

    duration = booking.end_time - booking.start_time
    new_end = new_start + duration

    # Load resource (may change)
    resource = resources_dal.get_resource_or_404(new_resource_id)

    downtime = (
        DowntimeBlock.query
        .filter_by(resource_id=resource.id)
        .filter(
            DowntimeBlock.start_time < new_end,
            DowntimeBlock.end_time > new_start
        )
        .first()
    )
    if downtime:
        return jsonify({
            "success": False,
            "message": (
                f"Cannot move booking into downtime "
                f"{downtime.start_time.strftime('%b %d %I:%M %p')} - "
                f"{downtime.end_time.strftime('%I:%M %p')}."
            )
        }), 409

    # Capacity / conflict check ignoring current booking
    conflict = (
        Booking.query
        .filter(
            Booking.resource_id == resource.id,
            Booking.id != booking.id,
            Booking.status.in_(["pending", "approved"]),
            Booking.start_time < new_end,
            Booking.end_time > new_start
        )
        .first()
    )

    if conflict:
        return jsonify({
            "success": False,
            "message": f"Conflicts with booking #{conflict.id} ({conflict.start_time.strftime('%b %d %I:%M %p')} - {conflict.end_time.strftime('%I:%M %p')})."
        }), 409

    # Update booking details
    booking.resource_id = resource.id
    booking.start_time = new_start
    booking.end_time = new_end
    booking.updated_at = datetime.now(timezone.utc)

    # Auto-approve if moved to public resource and still pending
    if booking.status == "pending" and resource.access_type == "public":
        booking.status = "approved"
        booking.approved_by = current_user.id

    # Notify user about change
    change_message = (
        f"Your booking for {resource.title} has been rescheduled to "
        f"{new_start.strftime('%b %d, %Y %I:%M %p')} - {new_end.strftime('%I:%M %p')}."
    )
    send_notification(
        booking.user,
        title="Booking Rescheduled",
        message=change_message,
        notification_type="booking_updated",
        related_url=url_for("booking.dashboard"),
    )

    # Record message trail if booking originated from a request
    if hasattr(booking, "request") and booking.request:
        message = Message(
            sender_id=current_user.id,
            receiver_id=booking.user_id,
            request_id=booking.request.id,
            subject="Booking rescheduled",
            content=change_message
        )
        db.session.add(message)

    db.session.commit()

    return jsonify({
        "success": True,
        "booking": {
            "id": booking.id,
            "resource_id": booking.resource_id,
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "status": booking.status
        }
    })