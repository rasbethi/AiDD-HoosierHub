from datetime import datetime, timezone, timedelta, time

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from src.models.models import (
    db,
    Resource,
    Booking,
    Waitlist,
    BookingRequest,
    Message,
    User,
    DowntimeBlock,
    Review,
    ResourceConversation,
    ResourceConversationMessage,
    SitePage,
)
from src.data_access import resources_dal, bookings_dal
from src.services.notification_service import send_notification
from src.services.booking_service import create_owner_booking_request
from src.services.external_search import fetch_related_terms
from src.services.booking_rules import (
    validate_time_block,
    ensure_capacity,
)
from src.services.slot_service import build_slot_days
from src.services.waitlist_service import promote_waitlist_entry
from src.utils.db_helpers import get_or_404

resource_bp = Blueprint("resource_bp", __name__, url_prefix="/resources")


STOCK_IMAGE_GROUPS = [
    {
        "label": "Study Group",
        "images": [
            "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?w=900&h=600&fit=crop",
        ],
    },
    {
        "label": "Peer Tutoring Circle",
        "images": [
            "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1448932223592-d1fc686e76ea?w=900&h=600&fit=crop",
        ],
    },
    {
        "label": "Club Resource",
        "images": [
            "https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=900&h=600&fit=crop",
        ],
    },
    {
        "label": "Case Prep Room",
        "images": [
            "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=900&h=600&fit=crop",
        ],
    },
    {
        "label": "Workshop / Skill Swap",
        "images": [
            "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1573164713670-8956dcd12e2d?w=900&h=600&fit=crop",
        ],
    },
    {
        "label": "Project Team Hub",
        "images": [
            "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?w=900&h=600&fit=crop",
        ],
    },
    {
        "label": "Community Meetup",
        "images": [
            "https://images.unsplash.com/photo-1461532257246-777de18cd58b?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=900&h=600&fit=crop",
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=900&h=600&fit=crop",
        ],
    },
]

BASIC_STUDENT_CATEGORIES = [
    "Study Group",
    "Peer Tutoring Circle",
    "Club Resource",
    "Case Prep Room",
    "Workshop / Skill Swap",
    "Project Team Hub",
    "Community Meetup"
]
BASIC_CATEGORY_SET = {label.lower(): label for label in BASIC_STUDENT_CATEGORIES}


# --------------------------
# PUBLIC PREVIEW PAGE (NO LOGIN REQUIRED)
# --------------------------
@resource_bp.route("/preview")
def preview_resources():
    """Show a preview of resources to guests and highlight real feedback."""
    featured_resources = (
        Resource.query
        .filter(Resource.status == Resource.STATUS_PUBLISHED)
        .order_by(Resource.created_at.desc())
        .limit(6)
        .all()
    )

    review_samples = (
        Review.query
        .filter(Review.comment.isnot(None))
        .order_by(Review.created_at.desc())
        .limit(6)
        .all()
    )

    about_page = SitePage.query.filter_by(slug="about").first()
    contact_page = SitePage.query.filter_by(slug="contact").first()

    contact_details = {
        "title": "Get in Touch",
        "subtitle": "Have a question, feedback, or need support? We'd love to hear from you.",
        "email": "support@campushub.edu",
        "phone": "(812) 555-0100",
        "location": "Luddy Hall, Indiana University",
        "hours": "Mon-Fri: 8 AM - 6 PM",
        "cta_text": "Email Us",
        "cta_href": "mailto:support@campushub.edu",
    }
    contact_html = None

    if contact_page and contact_page.body:
        parsed_contact = False
        for raw_line in contact_page.body.splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            val = value.strip()
            if key in contact_details and val:
                contact_details[key] = val
                parsed_contact = True
        if not parsed_contact:
            contact_html = contact_page.body

    if (not contact_details.get("cta_href")) and contact_details.get("email"):
        contact_details["cta_href"] = f"mailto:{contact_details['email']}"

    return render_template(
        "resources/preview.html",
        resources=featured_resources,
        review_samples=review_samples,
        about_page=about_page,
        contact_details=contact_details,
        contact_html=contact_html,
    )


# --------------------------
# FULL RESOURCE LIST (LOGIN REQUIRED)
# --------------------------
@resource_bp.route("/")
@login_required
def list_resources():
    """List all available resources with filters."""
    
    category_filter = request.args.get('category', '')
    access_filter = request.args.get('access', '')
    search_query = (request.args.get('search', '') or '').strip()
    min_capacity = request.args.get('min_capacity', type=int)
    availability_start = request.args.get('start_time', '')
    availability_end = request.args.get('end_time', '')
    sort_option = request.args.get('sort', 'recent')
    advanced_mode = request.args.get('advanced', type=int) == 1

    query = Resource.query.filter(Resource.status == Resource.STATUS_PUBLISHED)

    if category_filter:
        query = query.filter_by(category=category_filter)

    if access_filter:
        query = query.filter_by(access_type=access_filter)


    if min_capacity:
        query = query.filter(Resource.capacity >= min_capacity)

    google_search_enabled = current_app.config.get("GOOGLE_SEARCH_ENABLED", False)
    related_terms = []
    if search_query:
        search_filters = [
            Resource.title.ilike(f'%{search_query}%'),
            Resource.description.ilike(f'%{search_query}%'),
            Resource.location.ilike(f'%{search_query}%')
        ]

        if advanced_mode and google_search_enabled:
            related_terms = fetch_related_terms(search_query)
            for term in related_terms:
                search_filters.extend([
                    Resource.title.ilike(f'%{term}%'),
                    Resource.description.ilike(f'%{term}%'),
                    Resource.location.ilike(f'%{term}%')
                ])

        query = query.filter(or_(*search_filters))
    else:
        advanced_mode = False

    resources = query.all()

    availability_start_dt = None
    availability_end_dt = None
    if availability_start and availability_end:
        try:
            availability_start_dt = datetime.strptime(availability_start, "%Y-%m-%dT%H:%M")
            availability_end_dt = datetime.strptime(availability_end, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid availability window provided.", "warning")
            availability_start_dt = None
            availability_end_dt = None

    if availability_start_dt and availability_end_dt and availability_start_dt < availability_end_dt:
        resources = [
            resource for resource in resources
            if resource.get_available_slots(availability_start_dt, availability_end_dt) > 0
        ]

    def booking_count(resource):
        return sum(1 for booking in resource.bookings if booking.status in ("approved", "pending"))

    if sort_option == "most_booked":
        resources.sort(key=booking_count, reverse=True)
    elif sort_option == "top_rated":
        resources.sort(key=lambda r: r.average_rating(), reverse=True)
    else:
        resources.sort(key=lambda r: r.created_at or datetime.min, reverse=True)

    categories = db.session.query(Resource.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]

    spotlight_reviews = []
    for res in resources:
        for rev in res.reviews:
            if rev.comment:
                spotlight_reviews.append(rev)

    spotlight_reviews.sort(key=lambda r: r.created_at or datetime.min, reverse=True)
    spotlight_reviews = spotlight_reviews[:3]

    return render_template(
        "resources/list.html",
        resources=resources,
        categories=categories,
        current_category=category_filter,
        current_access=access_filter,
        search_query=search_query,
        min_capacity=min_capacity,
        availability_start=availability_start,
        availability_end=availability_end,
        sort_option=sort_option,
        advanced_mode=advanced_mode and google_search_enabled,
        google_search_enabled=google_search_enabled,
        related_terms=related_terms,
        spotlight_reviews=spotlight_reviews
    )


# --------------------------
# OWNER REQUESTS INBOX
# --------------------------
@resource_bp.route("/owner/requests")
@login_required
def owner_requests():
    """Allow resource owners to review booking requests and conversation threads."""
    owns_resources = Resource.query.filter_by(owner_id=current_user.id).first() is not None

    requests = []
    pending_count = 0
    if owns_resources:
        requests = (
            BookingRequest.query
            .join(Resource, BookingRequest.resource_id == Resource.id)
            .filter(Resource.owner_id == current_user.id, BookingRequest.kind == "owner")
            .order_by(BookingRequest.created_at.desc())
            .all()
        )
        pending_count = sum(1 for item in requests if item.status == "pending")

    conversations = (
        ResourceConversation.query
        .filter(or_(ResourceConversation.owner_id == current_user.id, ResourceConversation.requester_id == current_user.id))
        .order_by(ResourceConversation.updated_at.desc())
        .all()
    )

    return render_template(
        "resources/owner_inbox.html",
        requests=requests,
        pending_count=pending_count,
        conversations=conversations,
        owns_resources=owns_resources,
    )


@resource_bp.route("/<int:resource_id>/message-owner", methods=["POST"])
@login_required
def message_owner(resource_id):
    resource = resources_dal.get_resource_or_404(resource_id)
    redirect_to = request.form.get("return_to") or url_for("resource_bp.resource_detail", resource_id=resource_id)

    if not resource.owner_id:
        flash("This resource currently has no owner to message.", "info")
        return redirect(redirect_to)

    if resource.owner_id == current_user.id:
        flash("You already own this resource.", "info")
        return redirect(redirect_to)

    content = (request.form.get("content") or "").strip()
    if not content:
        flash("Message cannot be empty.", "warning")
        return redirect(redirect_to)

    conversation = (
        ResourceConversation.query
        .filter_by(resource_id=resource.id, requester_id=current_user.id)
        .first()
    )
    if not conversation:
        conversation = ResourceConversation(
            resource_id=resource.id,
            owner_id=resource.owner_id,
            requester_id=current_user.id,
        )
        db.session.add(conversation)
        db.session.flush()

    message = ResourceConversationMessage(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(message)
    conversation.updated_at = datetime.now(timezone.utc)

    send_notification(
        conversation.owner,
        title=f"New message about {resource.title}",
        message=content,
        notification_type="resource_message",
        related_url=url_for("resource_bp.owner_requests")
    )

    db.session.commit()
    flash("Message sent to the owner.", "success")
    return redirect(redirect_to)


@resource_bp.route("/conversations/<int:conversation_id>/message", methods=["POST"])
@login_required
def reply_to_conversation(conversation_id):
    conversation = get_or_404(ResourceConversation, conversation_id)
    permitted = current_user.id in (conversation.owner_id, conversation.requester_id)
    if not permitted:
        abort(403)

    content = (request.form.get("content") or "").strip()
    if not content:
        flash("Message cannot be empty.", "warning")
        return redirect(request.referrer or url_for("resource_bp.owner_requests"))

    message = ResourceConversationMessage(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(message)
    conversation.updated_at = datetime.now(timezone.utc)

    if current_user.id == conversation.requester_id:
        recipient = conversation.owner
    else:
        recipient = conversation.requester

    send_notification(
        recipient,
        title=f"New message about {conversation.resource.title}",
        message=content,
        notification_type="resource_message",
        related_url=url_for("resource_bp.owner_requests")
        if recipient.id == conversation.owner_id
        else url_for("resource_bp.resource_detail", resource_id=conversation.resource_id)
    )

    db.session.commit()
    flash("Message sent.", "success")
    return redirect(request.form.get("return_to") or request.referrer or url_for("resource_bp.owner_requests"))


# --------------------------
# POST MESSAGE ON REQUEST THREAD
# --------------------------
@resource_bp.route("/requests/<int:request_id>/message", methods=["POST"])
@login_required
def send_request_message(request_id):
    """Allow requester or resource owner to send a threaded message."""
    booking_request = get_or_404(BookingRequest, request_id)
    resource = booking_request.resource

    permitted = (
        current_user.is_admin()
        or current_user.id == booking_request.requester_id
        or current_user.id == resource.owner_id
    )
    if not permitted:
        abort(403)

    content = (request.form.get("content") or "").strip()
    if not content:
        flash("Message cannot be empty.", "warning")
        return redirect(request.referrer or url_for("resource_bp.resource_detail", resource_id=resource.id))

    if current_user.id == booking_request.requester_id:
        recipient = resource.owner
    else:
        recipient = booking_request.requester

    message = Message(
        sender_id=current_user.id,
        receiver_id=recipient.id,
        request_id=booking_request.id,
        subject=f"Message regarding {resource.title}",
        content=content
    )
    db.session.add(message)

    send_notification(
        recipient,
        title=f"New message about {resource.title}",
        message=content,
        notification_type="request_message",
        related_url=url_for("resource_bp.resource_detail", resource_id=resource.id)
    )

    db.session.commit()

    flash("Message sent.", "success")
    return redirect(request.referrer or url_for("resource_bp.resource_detail", resource_id=resource.id))


# --------------------------
# OWNER RESOURCES OVERVIEW
# --------------------------
@resource_bp.route("/mine")
@login_required
def owner_resources():
    resources = (
        Resource.query
        .filter_by(owner_id=current_user.id)
        .order_by(Resource.created_at.desc())
        .all()
    )
    return render_template("resources/mine.html", resources=resources)


# --------------------------
# OWNER BOOKINGS OVERVIEW
# --------------------------
@resource_bp.route("/mine/bookings")
@login_required
def owner_resource_bookings():
    bookings = (
        Booking.query
        .join(Resource, Booking.resource_id == Resource.id)
        .filter(Resource.owner_id == current_user.id)
        .order_by(Booking.start_time.desc())
        .all()
    )
    return render_template("resources/mine_bookings.html", bookings=bookings)


@resource_bp.route("/bookings/<int:booking_id>/owner/approve", methods=["POST"])
@login_required
def owner_approve_booking(booking_id):
    booking = bookings_dal.get_booking_or_404(booking_id)
    resource = booking.resource
    redirect_to = request.form.get("redirect_to")

    if resource.owner_id != current_user.id:
        abort(403)

    if booking.status != "pending":
        flash("This booking is no longer pending.", "info")
        return redirect(redirect_to or request.referrer or url_for("resource_bp.owner_resource_bookings"))

    try:
        ensure_capacity(resource, booking.start_time, booking.end_time, exclude_booking_id=booking.id)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(redirect_to or request.referrer or url_for("resource_bp.owner_resource_bookings"))

    if booking.request:
        booking.request.mark("approved", "Approved by owner")

    booking.status = "approved"
    booking.approved_by = current_user.id
    booking.decision_at = datetime.now(timezone.utc)
    db.session.commit()

    send_notification(
        booking.user,
        title="Booking approved",
        message=f"Your booking for {resource.title} starting {booking.start_time.strftime('%b %d, %Y %I:%M %p')} has been approved.",
        notification_type="booking_update",
        related_url=url_for("booking.dashboard")
    )

    flash("Booking approved and the user has been notified.", "success")
    return redirect(redirect_to or request.referrer or url_for("resource_bp.owner_resource_bookings"))


@resource_bp.route("/bookings/<int:booking_id>/owner/reject", methods=["POST"])
@login_required
def owner_reject_booking(booking_id):
    booking = bookings_dal.get_booking_or_404(booking_id)
    resource = booking.resource
    redirect_to = request.form.get("redirect_to")

    if resource.owner_id != current_user.id:
        abort(403)

    if booking.status != "pending":
        flash("This booking is no longer pending.", "info")
        return redirect(redirect_to or request.referrer or url_for("resource_bp.owner_resource_bookings"))

    reason = request.form.get("reason", "").strip()
    slot_start = booking.start_time
    slot_end = booking.end_time

    if booking.request:
        booking.request.mark("denied", reason or None)

    booking.status = "rejected"
    booking.decision_at = datetime.now(timezone.utc)
    booking.rejection_reason = reason or None

    db.session.flush()
    promoted_booking = promote_waitlist_entry(resource, slot_start, slot_end, actor=current_user)

    send_notification(
        booking.user,
        title="Booking rejected",
        message=(
            f"Your booking for {resource.title} starting "
            f"{booking.start_time.strftime('%b %d, %Y %I:%M %p')} was rejected."
            + (f" Reason: {reason}" if reason else "")
        ),
        notification_type="booking_update",
        related_url=url_for("booking.dashboard")
    )

    if promoted_booking:
        flash("Slot reassigned to the next person on the waitlist.", "info")

    db.session.commit()
    flash("Booking rejected and the user has been notified.", "info")
    return redirect(redirect_to or request.referrer or url_for("resource_bp.owner_resource_bookings"))


# --------------------------
# RESOURCE DETAIL PAGE
# --------------------------
@resource_bp.route("/<int:resource_id>")
@login_required
def resource_detail(resource_id):
    """Show detailed view of a single resource."""
    resource = resources_dal.get_resource_or_404(resource_id)

    if (resource.status != Resource.STATUS_PUBLISHED and
            not (current_user.is_authenticated and (current_user.id == resource.owner_id or current_user.is_admin()))):
        flash("This resource is not currently available.", "warning")
        return redirect(url_for("resource_bp.list_resources"))

    reviews = (
        Review.query
        .filter_by(resource_id=resource_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    user_booking = None
    waitlist_entries = []
    if current_user.role in ("student", "staff"):
        waitlist_entries = (
            Waitlist.query
            .filter_by(resource_id=resource_id, user_id=current_user.id, status="waiting")
            .order_by(Waitlist.created_at.desc())
            .all()
        )
    is_favorite = current_user in resource.favorited_by
    latest_request = (
        BookingRequest.query.filter_by(
            resource_id=resource_id,
            requester_id=current_user.id
        )
        .order_by(BookingRequest.created_at.desc())
        .first()
    )
    latest_request_messages = []
    if latest_request:
        latest_request_messages = sorted(
            latest_request.messages,
            key=lambda msg: msg.created_at or datetime.min
        )
    is_owner = current_user.id == resource.owner_id
    pending_owner_bookings = []
    if is_owner:
        pending_owner_bookings = (
            Booking.query
            .filter_by(resource_id=resource_id, status="pending")
            .order_by(Booking.start_time.asc())
            .all()
        )

    conversation = None
    conversation_messages = []
    can_message_owner = (
        current_user.is_authenticated
        and resource.owner_id
        and current_user.id != resource.owner_id
    )
    if can_message_owner:
        conversation = (
            ResourceConversation.query
            .filter_by(resource_id=resource.id, requester_id=current_user.id)
            .first()
        )
        if conversation:
            conversation_messages = sorted(
                conversation.messages,
                key=lambda msg: msg.created_at or datetime.min
            )

    slot_anchor_param = request.args.get("date")
    slot_anchor = None
    now = datetime.now()
    if slot_anchor_param:
        try:
            slot_anchor = datetime.strptime(slot_anchor_param, "%Y-%m-%d")
        except ValueError:
            slot_anchor = None
    if slot_anchor:
        if slot_anchor.date() == now.date():
            slot_anchor = now
        elif slot_anchor < now:
            slot_anchor = now
    slot_days = build_slot_days(resource, start_time=slot_anchor)
    today_iso = datetime.now(timezone.utc).date().isoformat()
    selected_date_iso = slot_anchor.date().isoformat() if slot_anchor else today_iso

    can_review = False
    existing_review = None
    has_completed_booking = False
    if current_user.role in ("student", "staff") and resource.owner_id != current_user.id:
        completed_booking = (
            Booking.query
            .filter(
                Booking.resource_id == resource_id,
                Booking.user_id == current_user.id,
                Booking.status == "approved",
                Booking.end_time <= datetime.now(timezone.utc),
            )
            .order_by(Booking.end_time.desc())
            .first()
        )
        if completed_booking:
            has_completed_booking = True
            existing_review = (
                Review.query
                .filter_by(resource_id=resource_id, reviewer_id=current_user.id)
                .order_by(Review.created_at.desc())
                .first()
            )
            can_review = existing_review is None

    return render_template(
        "resources/detail.html",
        resource=resource,
        reviews=reviews,
        user_booking=user_booking,
        waitlist_entries=waitlist_entries,
        is_favorite=is_favorite,
        latest_request=latest_request,
        latest_request_messages=latest_request_messages,
        is_owner=is_owner,
        pending_owner_bookings=pending_owner_bookings,
        slot_days=slot_days,
        today_iso=today_iso,
        selected_date_iso=selected_date_iso,
        can_review=can_review,
        existing_review=existing_review,
        has_completed_booking=has_completed_booking,
        conversation=conversation,
        conversation_messages=conversation_messages,
        can_message_owner=can_message_owner
    )


@resource_bp.route("/<int:resource_id>/book", methods=["POST"])
@login_required
def book_resource(resource_id):
    """Create a booking request for a resource."""
    resource = resources_dal.get_resource_or_404(resource_id)

    if current_user.is_admin():
        flash("Admins allocate resources from the dashboard. Use the admin tools instead of booking here.", "info")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    start_time_raw = request.form.get("start_time")
    end_time_raw = request.form.get("end_time")
    purpose = request.form.get("purpose", "").strip()

    if not start_time_raw or not end_time_raw:
        flash("Please select both a start and end time.", "warning")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    try:
        start_time = datetime.strptime(start_time_raw, "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(end_time_raw, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Invalid date format. Please use the provided date pickers.", "danger")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))
    try:
        validate_time_block(start_time, end_time)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    recurrence = request.form.get("recurrence", "none")
    recurrence_count = request.form.get("recurrence_count", type=int) or 1
    recurrence_count = max(1, min(recurrence_count, 10))

    delta_lookup = {
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
    }

    occurrences = [(start_time, end_time)]
    if recurrence in delta_lookup and recurrence_count > 1:
        delta = delta_lookup[recurrence]
        for i in range(1, recurrence_count):
            occ_start = start_time + i * delta
            occ_end = end_time + i * delta
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
            return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

        try:
            ensure_capacity(resource, occ_start, occ_end)
        except ValueError as exc:
            flash(str(exc), "warning")
            return redirect(
                url_for(
                    "resource_bp.resource_detail",
                    resource_id=resource_id,
                    waitlist="1",
                    wait_start=start_time.strftime("%Y-%m-%dT%H:%M"),
                    wait_end=end_time.strftime("%Y-%m-%dT%H:%M"),
                    wait_purpose=purpose
                )
            )

    # Allow multiple bookings even if user already has one pending/approved
    is_owner_booking = resource.owner_id == current_user.id
    auto_approve = resource.access_type == "public" or is_owner_booking

    bookings_created = []
    for occ_start, occ_end in occurrences:
        booking = Booking(
            resource_id=resource_id,
            user_id=current_user.id,
            start_time=occ_start,
            end_time=occ_end,
            purpose=purpose or f"Booking request by {current_user.name}",
            status="approved" if auto_approve else "pending",
            approved_by=current_user.id if auto_approve else None,
            decision_at=datetime.now(timezone.utc) if auto_approve else None
        )
        db.session.add(booking)
        db.session.flush()

        if not auto_approve:
            create_owner_booking_request(resource, booking, current_user, purpose)

        bookings_created.append(booking)

    db.session.commit()

    if auto_approve:
        flash(f"{len(bookings_created)} booking{'s' if len(bookings_created) > 1 else ''} confirmed! You're all set.", "success")
    else:
        flash("Booking request submitted! You'll be notified once it's reviewed.", "success")
    return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))


@resource_bp.route("/<int:resource_id>/self-book", methods=["POST"])
@login_required
def self_book_resource(resource_id):
    """Allow resource owners (staff or students) to instantly book their own resource."""
    resource = resources_dal.get_resource_or_404(resource_id)

    if resource.owner_id != current_user.id:
        abort(403)

    start_time_raw = request.form.get("start_time")
    end_time_raw = request.form.get("end_time")
    purpose = (request.form.get("purpose") or "Owner self-booking").strip()

    if not start_time_raw or not end_time_raw:
        flash("Please select both start and end time.", "warning")
        return redirect(request.referrer or url_for("resource_bp.list_resources"))

    try:
        start_time = datetime.strptime(start_time_raw, "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(end_time_raw, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Invalid date format.", "danger")
        return redirect(request.referrer or url_for("resource_bp.list_resources"))
    try:
        validate_time_block(start_time, end_time)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(request.referrer or url_for("resource_bp.list_resources"))

    downtime = (
        DowntimeBlock.query
        .filter_by(resource_id=resource_id)
        .filter(
            DowntimeBlock.start_time < end_time,
            DowntimeBlock.end_time > start_time
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
        return redirect(request.referrer or url_for("resource_bp.list_resources"))

    try:
        ensure_capacity(resource, start_time, end_time)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(request.referrer or url_for("resource_bp.list_resources"))

    booking = Booking(
        resource_id=resource_id,
        user_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        purpose=purpose,
        status="approved",
        approved_by=current_user.id,
        decision_at=datetime.now(timezone.utc)
    )
    db.session.add(booking)
    db.session.commit()

    flash(f"{resource.title} is booked for you!", "success")
    return redirect(request.referrer or url_for("resource_bp.list_resources"))


@resource_bp.route("/<int:resource_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(resource_id):
    """Mark or unmark a resource as a favorite."""
    resource = resources_dal.get_resource_or_404(resource_id)

    redirect_url = request.form.get("next") or url_for("resource_bp.resource_detail", resource_id=resource_id)

    if current_user in resource.favorited_by:
        resource.favorited_by.remove(current_user)
        db.session.commit()
        flash(f"Removed '{resource.title}' from your favorites.", "info")
    else:
        resource.favorited_by.append(current_user)
        db.session.commit()
        flash(f"Added '{resource.title}' to your favorites.", "success")

    return redirect(redirect_url)


# --------------------------
# CREATE NEW RESOURCE
# --------------------------
@resource_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_resource():
    """Create a new resource."""
    owner_options = []
    if current_user.is_admin():
        owner_options = (
            User.query
            .filter(User.role.in_(["student", "staff"]), User.status == "active")
            .order_by(User.name.asc())
            .all()
        )

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = (request.form.get("category") or "").strip()
        capacity = request.form.get("capacity", 1, type=int)
        location = request.form.get("location")
        available_slots = request.form.get("available_slots", 10, type=int)
        image_url = request.form.get("image_url", "https://picsum.photos/400/300")
        
        is_privileged = current_user.is_staff() or current_user.is_admin()
        access_type = request.form.get("access_type", "restricted" if is_privileged else "public")

        if current_user.is_admin():
            owner_id = request.form.get("owner_id", type=int)
            owner = db.session.get(User, owner_id) if owner_id else None
            if not owner or owner.role not in ("student", "staff"):
                flash("Select a valid student or staff owner for this resource.", "warning")
                return render_template(
                    "resources/create.html",
                    stock_image_groups=STOCK_IMAGE_GROUPS,
                    owner_options=owner_options,
                    basic_categories=BASIC_STUDENT_CATEGORIES,
                    selected_category=category,
                )
            assigned_owner_id = owner.id
        else:
            if current_user.role not in ("student", "staff"):
                flash("Only student or staff accounts can own resources.", "danger")
                return redirect(url_for("resource_bp.list_resources"))
            assigned_owner_id = current_user.id
            if current_user.role == "student":
                if category.lower() not in BASIC_CATEGORY_SET:
                    flash("Students can only create basic community resources (study groups, peer tutoring, case prep, etc.). Please choose one from the list.", "warning")
                    return render_template(
                        "resources/create.html",
                        stock_image_groups=STOCK_IMAGE_GROUPS,
                        basic_categories=BASIC_STUDENT_CATEGORIES,
                        owner_options=owner_options,
                        selected_category=category,
                    )
                category = BASIC_CATEGORY_SET[category.lower()]
            else:
                normalized = category.strip()
                if normalized and normalized.lower() not in BASIC_CATEGORY_SET:
                    BASIC_STUDENT_CATEGORIES.append(normalized)
                    BASIC_CATEGORY_SET[normalized.lower()] = normalized

        new_resource = Resource(
            title=title,
            description=description,
            category=category,
            capacity=capacity,
            location=location,
            available_slots=available_slots,
            image_url=image_url,
            access_type=access_type,
            owner_id=assigned_owner_id,
            status=Resource.STATUS_PUBLISHED if is_privileged else Resource.STATUS_DRAFT
        )
        
        db.session.add(new_resource)
        db.session.commit()
        
        # Notify admins only when a student creates a draft that needs approval
        if current_user.role == "student":
            admin_users = User.query.filter_by(role="admin", status="active").all()
            resource_link = url_for("admin.manage_resources")
            for admin_user in admin_users:
                send_notification(
                    admin_user,
                    title="New resource awaiting approval",
                    message=(
                        f"{current_user.name} created '{title}'. "
                        "Review and publish it from the admin resources page."
                    ),
                    notification_type="resource_draft",
                    related_url=resource_link,
                )
            db.session.commit()

        flash(f"Resource '{title}' created successfully!", "success")
        return redirect(url_for("resource_bp.list_resources"))
    
    return render_template(
        "resources/create.html",
        stock_image_groups=STOCK_IMAGE_GROUPS,
        owner_options=owner_options,
        basic_categories=BASIC_STUDENT_CATEGORIES
    )


# --------------------------
# EDIT RESOURCE
# --------------------------
@resource_bp.route("/edit/<int:resource_id>", methods=["GET", "POST"])
@login_required
def edit_resource(resource_id):
    """Edit an existing resource."""
    
    resource = resources_dal.get_resource_or_404(resource_id)
    
    if current_user.id != resource.owner_id and not current_user.is_admin():
        flash("You don't have permission to edit this resource.", "danger")
        return redirect(url_for("resource_bp.list_resources"))

    owner_options = []
    if current_user.is_admin():
        owner_options = (
            User.query
            .filter(User.role.in_(["student", "staff"]), User.status == "active")
            .order_by(User.name.asc())
            .all()
        )
    
    owner_role = resource.owner.role if resource.owner else None

    if request.method == "POST":
        resource.title = request.form.get("title")
        resource.description = request.form.get("description")
        category_value = (request.form.get("category") or "").strip()
        if owner_role == "student":
            if category_value.lower() not in BASIC_CATEGORY_SET:
                flash("Student-owned resources must stay within the basic categories (study groups, peer tutoring, etc.).", "warning")
                return render_template(
                    "resources/edit.html",
                    resource=resource,
                    owner_options=owner_options,
                    basic_categories=BASIC_STUDENT_CATEGORIES
                )
            category_value = BASIC_CATEGORY_SET[category_value.lower()]
        elif owner_role == "staff":
            if category_value and category_value.lower() not in BASIC_CATEGORY_SET:
                BASIC_STUDENT_CATEGORIES.append(category_value)
                BASIC_CATEGORY_SET[category_value.lower()] = category_value
        resource.category = category_value
        resource.capacity = request.form.get("capacity", type=int)
        resource.location = request.form.get("location")
        resource.available_slots = request.form.get("available_slots", type=int)
        resource.image_url = request.form.get("image_url")
        
        if current_user.is_staff() or current_user.is_admin():
            resource.access_type = request.form.get("access_type")
        if current_user.is_admin():
            owner_id = request.form.get("owner_id", type=int)
            owner = db.session.get(User, owner_id) if owner_id else None
            if not owner or owner.role not in ("student", "staff"):
                flash("Select a valid student or staff owner.", "warning")
                return render_template("resources/edit.html", resource=resource, owner_options=owner_options)
            resource.owner_id = owner.id

        db.session.commit()
        flash(f"Resource '{resource.title}' updated successfully!", "success")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource.id))
    
    return render_template(
        "resources/edit.html",
        resource=resource,
        owner_options=owner_options,
        basic_categories=BASIC_STUDENT_CATEGORIES
    )


# --------------------------
# JOIN WAITLIST
# --------------------------
@resource_bp.route("/waitlist/<int:resource_id>", methods=["POST"])
@login_required
def join_waitlist(resource_id):
    """Add user to waitlist."""
    
    resource = resources_dal.get_resource_or_404(resource_id)
    redirect_target = request.referrer or url_for("resource_bp.resource_detail", resource_id=resource_id)

    start_time_raw = request.form.get("start_time")
    end_time_raw = request.form.get("end_time")
    purpose = (request.form.get("purpose") or "").strip()

    if not start_time_raw or not end_time_raw:
        flash("Select a start and end time to join the waitlist.", "warning")
        return redirect(redirect_target)

    try:
        start_time = datetime.strptime(start_time_raw, "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(end_time_raw, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Invalid date format. Please use the provided selectors.", "danger")
        return redirect(redirect_target)

    try:
        validate_time_block(start_time, end_time)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(redirect_target)
    
    existing = (
        Waitlist.query
        .filter_by(resource_id=resource_id, user_id=current_user.id)
        .filter(Waitlist.start_time == start_time, Waitlist.end_time == end_time)
        .first()
    )
    
    max_position = db.session.query(db.func.max(Waitlist.position)).filter_by(
        resource_id=resource_id
    ).scalar() or 0
    
    if existing:
        if existing.status == "waiting":
            flash("You're already on the waitlist for that time window.", "info")
            return redirect(redirect_target)
        existing.status = "waiting"
        existing.position = max_position + 1
        existing.created_at = datetime.now(timezone.utc)
        waitlist_entry = existing
    else:
        waitlist_entry = Waitlist(
            resource_id=resource_id,
            user_id=current_user.id,
            position=max_position + 1,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose or None,
            status="waiting"
        )
        db.session.add(waitlist_entry)
    db.session.commit()
    
    flash(
        f"Added to waitlist for {start_time.strftime('%b %d %I:%M %p')} – {end_time.strftime('%I:%M %p')}! "
        f"You're position #{waitlist_entry.position}.",
        "success",
    )
    return redirect(redirect_target)


# --------------------------
# REQUEST ADMIN ALLOCATION
# --------------------------
@resource_bp.route("/<int:resource_id>/request-admin", methods=["POST"])
@login_required
def request_admin_allocation(resource_id):
    resource = resources_dal.get_resource_or_404(resource_id)

    if current_user.is_admin():
        flash("Admins can allocate resources directly from the dashboard.", "info")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    start_time_raw = request.form.get("start_time")
    end_time_raw = request.form.get("end_time")
    purpose = request.form.get("purpose", "").strip()
    note = request.form.get("note", "").strip()

    if not start_time_raw or not end_time_raw:
        flash("Please include both a start and end time for your request.", "warning")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    try:
        start_time = datetime.strptime(start_time_raw, "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(end_time_raw, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Invalid date format. Please use the provided date pickers.", "danger")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))
    try:
        validate_time_block(start_time, end_time)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    try:
        ensure_capacity(resource, start_time, end_time)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(
            url_for(
                "resource_bp.resource_detail",
                resource_id=resource_id,
                waitlist="1",
                wait_start=start_time.strftime("%Y-%m-%dT%H:%M"),
                wait_end=end_time.strftime("%Y-%m-%dT%H:%M"),
                wait_purpose=purpose
            )
        )

    existing_pending = BookingRequest.query.filter_by(
        resource_id=resource_id,
        requester_id=current_user.id,
        status="pending",
        kind="allocator"
    ).first()

    if existing_pending:
        flash("You already have a pending request for this resource. Please wait for an admin to respond.", "info")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    booking_request = BookingRequest(
        resource_id=resource_id,
        requester_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        purpose=purpose,
        note=note,
        kind="allocator"
    )

    db.session.add(booking_request)
    db.session.flush()  # Ensure we have an ID for related records

    # Create an initial message for the admin trail
    admin_recipient = User.query.filter_by(role="admin").order_by(User.created_at.asc()).first()
    message_body = note or (
        f"{current_user.name} requested an admin booking from "
        f"{start_time.strftime('%b %d %I:%M %p')} to {end_time.strftime('%b %d %I:%M %p')}."
    )

    if admin_recipient:
        initial_message = Message(
            sender_id=current_user.id,
            receiver_id=admin_recipient.id,
            request_id=booking_request.id,
            subject=f"Booking request for {resource.title}",
            content=message_body
        )
        db.session.add(initial_message)

    # Notify all admins
    admin_users = User.query.filter_by(role="admin").all()
    request_link = url_for("admin.view_request", request_id=booking_request.id)

    for admin_user in admin_users:
        send_notification(
            admin_user,
            title="New Booking Request",
            message=f"{current_user.name} requested an admin booking for {resource.title}.",
            notification_type="booking_request",
            related_url=request_link,
        )

    db.session.commit()

    flash("Your request has been sent to the admin team. You'll be notified once it's reviewed.", "success")
    return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))


@resource_bp.route("/<int:resource_id>/reviews", methods=["POST"])
@login_required
def submit_review(resource_id):
    resource = resources_dal.get_resource_or_404(resource_id)

    if current_user.role not in ("student", "staff"):
        flash("Only students and staff can leave reviews.", "warning")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    if resource.owner_id == current_user.id:
        flash("You can't review a resource you own.", "warning")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    rating = request.form.get("rating", type=int)
    comment = (request.form.get("comment") or "").strip()

    if rating is None or rating < 1 or rating > 5:
        flash("Select a rating between 1 and 5 stars.", "warning")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    completed_booking = (
        Booking.query
        .filter(
            Booking.resource_id == resource_id,
            Booking.user_id == current_user.id,
            Booking.status == "approved",
            Booking.end_time <= datetime.now(timezone.utc),
        )
        .order_by(Booking.end_time.desc())
        .first()
    )

    if not completed_booking:
        flash("You need a completed booking before leaving a review.", "info")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    existing_review = Review.query.filter_by(
        resource_id=resource_id, reviewer_id=current_user.id
    ).first()

    if existing_review:
        flash("You've already reviewed this resource.", "info")
        return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))

    review = Review(
        resource_id=resource_id,
        reviewer_id=current_user.id,
        rating=rating,
        comment=comment or None,
    )
    db.session.add(review)
    db.session.commit()

    flash("Thanks for sharing your experience!", "success")
    return redirect(url_for("resource_bp.resource_detail", resource_id=resource_id))