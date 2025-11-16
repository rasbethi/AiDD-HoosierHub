from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import current_user

from src.services.chatbot_service import gemini_enabled, suggest_actions_with_llm
from src.services.concierge_service import concierge_response

assistant_bp = Blueprint("assistant", __name__, url_prefix="/assistant")

ASSISTANT_ACTIONS = [
    # General user actions
    {
        "id": "book_resource",
        "label": "Book a Resource",
        "description": "Open the booking form for rooms, labs, or equipment.",
        "url": "/resources/",
        "keywords": ["book", "booking", "reserve", "room", "lab", "space", "how do i book", "reserve a room"],
        "roles": ["student", "staff", "admin"],
        "featured": True,
    },
    {
        "id": "browse_resources",
        "label": "Browse Resources",
        "description": "Search or filter the full catalog.",
        "url": "/resources/",
        "keywords": ["browse", "explore", "search resources", "show resources", "filter", "categories"],
        "roles": ["student", "staff", "admin"],
    },
    {
        "id": "preview_resources",
        "label": "Preview Resources",
        "description": "See featured spaces without logging in.",
        "url": "/resources/preview",
        "keywords": ["preview", "guest", "demo", "public landing"],
        "roles": ["guest"],
        "featured": True,
    },
    {
        "id": "my_bookings",
        "label": "My Bookings",
        "description": "Review or cancel bookings you created.",
        "url": "/bookings/",
        "keywords": ["my bookings", "upcoming bookings", "calendar", "download ical"],
        "roles": ["student", "staff", "admin"],
        "featured": True,
    },
    {
        "id": "calendar_export",
        "label": "Download iCal",
        "description": "Export bookings to Google, Outlook, or Apple calendars.",
        "url": "/bookings/",
        "keywords": ["calendar export", "ics", "outlook", "google calendar"],
        "roles": ["student", "staff", "admin"],
    },
    {
        "id": "favorites",
        "label": "Favorite Resources",
        "description": "Track spaces you starred for quick access.",
        "url": "/resources/",
        "keywords": ["favorite", "starred", "saved spaces"],
        "roles": ["student", "staff", "admin"],
    },
    # Owner tools
    {
        "id": "owner_resources",
        "label": "My Resources",
        "description": "Manage listings you own.",
        "url": "/resources/mine",
        "keywords": ["my resources", "owned", "manage listing", "edit resource"],
        "roles": ["student", "staff", "admin"],
        "featured": True,
    },
    {
        "id": "owner_resource_bookings",
        "label": "Bookings for My Resources",
        "description": "See who is currently scheduled to use your spaces.",
        "url": "/resources/mine/bookings",
        "keywords": ["resource bookings", "usage", "schedule for my room"],
        "roles": ["student", "staff", "admin"],
    },
    {
        "id": "owner_inbox",
        "label": "Owner Requests Inbox",
        "description": "Approve or reject booking requests plus chat threads.",
        "url": "/resources/owner/requests",
        "keywords": ["approve", "reject", "owner inbox", "pending request", "messages"],
        "roles": ["student", "staff", "admin"],
    },
    {
        "id": "create_resource",
        "label": "Add New Resource",
        "description": "Publish a new room, lab, or equipment listing.",
        "url": "/resources/create",
        "keywords": ["add resource", "create listing", "publish space"],
        "roles": ["student", "staff", "admin"],
    },
    {
        "id": "self_book",
        "label": "Book My Own Resource",
        "description": "Instantly reserve a resource you own.",
        "url": "/resources/",
        "keywords": ["book my resource", "self book", "block my lab"],
        "roles": ["student", "staff", "admin"],
    },
    # Waitlist & requests
    {
        "id": "waitlist_help",
        "label": "Waitlist Help",
        "description": "See how to join or manage waitlists when slots are full.",
        "url": "/resources/",
        "keywords": ["waitlist", "capacity full", "slot full", "join waitlist"],
        "roles": ["student", "staff", "admin"],
        "featured": True,
    },
    {
        "id": "request_admin_booking",
        "label": "Request Admin Booking",
        "description": "Ask an admin to allocate a resource for you.",
        "url": "/resources/",
        "keywords": ["book for me", "admin help", "request booking"],
        "roles": ["student", "staff"],
    },
    {
        "id": "book_for_user",
        "label": "Book for a User",
        "description": "Admins can allocate resources on behalf of others.",
        "url": "/admin/book-for-user",
        "keywords": ["book for user", "allocate", "schedule for staff", "book for student"],
        "roles": ["admin"],
    },
    # Admin dashboards & insights
    {
        "id": "admin_dashboard",
        "label": "Admin Dashboard",
        "description": "SLA metrics, utilization, and quick actions.",
        "url": "/admin/",
        "keywords": ["admin dashboard", "sla", "analytics", "overview"],
        "roles": ["admin"],
        "featured": True,
    },
    {
        "id": "admin_sla",
        "label": "Approval SLA & Alerts",
        "description": "Check pending approvals over 24h and response time.",
        "url": "/admin/",
        "keywords": ["sla", "approval time", "overdue", "pending approvals"],
        "roles": ["admin"],
    },
    {
        "id": "admin_resources",
        "label": "Manage Resources",
        "description": "Draft/publish/archive, bulk actions, and quick filters.",
        "url": "/admin/resources",
        "keywords": ["manage resources", "bulk actions", "draft", "publish", "archive"],
        "roles": ["admin"],
    },
    {
        "id": "admin_users",
        "label": "Manage Users",
        "description": "Search users, toggle active status, view stats.",
        "url": "/admin/users",
        "keywords": ["manage users", "inactive", "activate", "user search"],
        "roles": ["admin"],
    },
    {
        "id": "admin_bookings",
        "label": "Manage All Bookings",
        "description": "Approve, reject, or delete bookings from one place.",
        "url": "/admin/bookings",
        "keywords": ["admin bookings", "approve booking", "reject", "booking detail"],
        "roles": ["admin"],
    },
    {
        "id": "admin_reviews",
        "label": "Moderate Reviews",
        "description": "Review feedback and remove inappropriate reviews.",
        "url": "/admin/reviews",
        "keywords": ["reviews", "feedback", "moderate"],
        "roles": ["admin"],
    },
    {
        "id": "admin_schedule",
        "label": "Scheduling Center",
        "description": "Multi-resource calendar with drag-to-reschedule and downtime blocks.",
        "url": "/admin/schedule",
        "keywords": ["schedule", "calendar", "reschedule", "downtime", "maintenance", "drag drop"],
        "roles": ["admin"],
    },
    {
        "id": "admin_requests",
        "label": "Admin Requests Inbox",
        "description": "Handle 'book for me' requests with threaded messaging.",
        "url": "/admin/requests",
        "keywords": ["requests", "inbox", "book for me", "allocate", "messages"],
        "roles": ["admin"],
    },
    {
        "id": "admin_unified_inbox",
        "label": "Unified Admin Inbox",
        "description": "Combined view of book-for-me requests and owner approvals.",
        "url": "/admin/inbox",
        "keywords": ["admin inbox", "review requests", "owner approvals", "book for me"],
        "roles": ["admin"],
        "featured": True,
    },
    {
        "id": "admin_email_log",
        "label": "Email Log",
        "description": "View simulated emails and notifications that were sent.",
        "url": "/admin/email-log",
        "keywords": ["email log", "notification log", "email history"],
        "roles": ["admin"],
    },
    {
        "id": "admin_analytics",
        "label": "Analytics & Utilization",
        "description": "Role-based usage, resource leaderboards, and SLA metrics.",
        "url": "/admin/",
        "keywords": ["analytics", "utilization", "reports", "stats", "metrics"],
        "roles": ["admin"],
    },
    # Misc utilities
    {
        "id": "help_menu",
        "label": "Show Full Menu",
        "description": "Display every action Nova can launch.",
        "url": "/assistant/",
        "keywords": ["menu", "options", "help", "what can you do"],
        "roles": ["guest", "student", "staff", "admin"],
    },
]

DEFAULT_QUICK_REPLIES = [
    "Show menu",
    "How do I book a resource?",
    "Show admin tools",
    "Waitlist help",
]


def _user_roles():
    if getattr(current_user, "is_authenticated", False):
        if current_user.is_admin():
            return ["admin", "staff", "student"]
        if current_user.is_staff():
            return ["staff", "student"]
        return ["student"]
    return ["guest"]


def _filter_actions_for_user():
    roles = _user_roles()
    accessible = []
    for action in ASSISTANT_ACTIONS:
        allowed = action.get("roles", ["student", "staff", "admin"])
        if any(role in allowed for role in roles):
            accessible.append(action)
    return accessible


def _featured_actions(accessible, limit=4):
    featured = [a for a in accessible if a.get("featured")]
    remaining = [a for a in accessible if not a.get("featured")]
    combined = featured + remaining
    seen = []
    for action in combined:
        if action["id"] not in seen:
            seen.append(action["id"])
            yield action
        if len(seen) >= limit:
            break


def _match_actions(query, accessible):
    q = query.lower()
    matches = []
    for action in accessible:
        keywords = action.get("keywords", [])
        if any(keyword in q for keyword in keywords):
            matches.append(action)
    return matches


def _build_default_reply():
    accessible = _filter_actions_for_user()
    suggestions = list(_featured_actions(accessible, limit=5))
    answer = "Here’s a quick menu of what I can help you with."
    return answer, suggestions


def _llm_reply(query: str, accessible_actions: list, roles: list):
    if not gemini_enabled():
        return None
    data = suggest_actions_with_llm(query, accessible_actions, roles)
    if not data:
        return None
    suggestion_ids = set(data.get("suggestion_ids") or [])
    suggestions = [
        action for action in accessible_actions if action["id"] in suggestion_ids
    ]
    answer = data.get("answer") or "Here’s what I can do for you."
    quick_replies = data.get("quick_replies") or DEFAULT_QUICK_REPLIES
    fallback = data.get("fallback", False)
    return {
        "answer": answer,
        "suggestions": suggestions,
        "quick_replies": quick_replies,
        "fallback": fallback,
    }


@assistant_bp.route("/")
def assistant_home():
    return render_template("assistant/assistant.html")


@assistant_bp.route('/ask', methods=['POST'])
def ask_assistant():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()

    accessible = _filter_actions_for_user()

    if not query:
        answer, suggestions = _build_default_reply()
        return jsonify({
            "answer": answer,
            "suggestions": suggestions,
            "quick_replies": DEFAULT_QUICK_REPLIES,
        })

    lower_query = query.lower()

    greetings = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}
    thanks_tokens = {"thanks", "thank you", "appreciate", "great"}

    if any(token in lower_query for token in greetings):
        answer, suggestions = _build_default_reply()
        answer = "Hi there! 👋 How can I help? Here are a few things I can do:"
        return jsonify({
            "answer": answer,
            "suggestions": suggestions,
            "quick_replies": DEFAULT_QUICK_REPLIES,
        })

    if any(token in lower_query for token in thanks_tokens):
        return jsonify({
            "answer": "Happy to help! Let me know if you need anything else.",
            "suggestions": [],
            "quick_replies": DEFAULT_QUICK_REPLIES,
        })

    if "menu" in lower_query or "options" in lower_query or "help" in lower_query:
        answer, suggestions = _build_default_reply()
        answer = "Here’s the latest menu of actions I can launch for you:"
        return jsonify({
            "answer": answer,
            "suggestions": suggestions,
            "quick_replies": DEFAULT_QUICK_REPLIES,
        })

    llm_result = _llm_reply(query, accessible, _user_roles())
    if llm_result and not llm_result.get("fallback"):
        return jsonify(llm_result)

    concierge = concierge_response(query)
    if concierge:
        return jsonify(concierge)

    matches = _match_actions(lower_query, accessible)

    if matches:
        limited_matches = matches[:5]
        if len(limited_matches) == 1:
            answer = f"You can use {limited_matches[0]['label']} to {limited_matches[0]['description'].lower()}."
        else:
            labels = ", ".join(action["label"] for action in limited_matches)
            answer = f"I found a few options that match: {labels}."

        return jsonify({
            "answer": answer,
            "suggestions": limited_matches,
            "quick_replies": DEFAULT_QUICK_REPLIES,
        })

    answer, suggestions = _build_default_reply()
    answer = (
        "I didn’t find an exact match for that, but here are a few useful sections. "
        "Let me know if you want something else!"
    )

    return jsonify({
        "answer": answer,
        "suggestions": suggestions,
        "quick_replies": DEFAULT_QUICK_REPLIES,
    })
