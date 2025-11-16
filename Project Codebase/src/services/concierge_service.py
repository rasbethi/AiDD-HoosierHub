from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from flask import current_app
from sqlalchemy import or_
from flask_login import current_user

from src.models.models import Resource


def _context_dir() -> Path:
    root = Path(current_app.root_path)
    return root / "docs" / "context"


def _clean_markdown(text: str) -> str:
    cleaned = text.replace("**", "").replace("__", "")
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"#+\s*", "", cleaned)
    cleaned = cleaned.replace("•", "-").replace("–", "-")
    cleaned = cleaned.replace("…", "… ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"(\d+\.)\s*", r"\n\1 ", cleaned)
    return cleaned.strip()


_DOC_CACHE: Optional[List[Dict[str, str]]] = None

MENU_SHORTCUTS: List[Dict[str, Any]] = [
    {
        "keywords": ["cancel", "cancel booking", "how to cancel", "cancel a booking", "delete booking"],
        "answer": "Click the button below to go to **My Bookings** where you can cancel or reschedule your reservations.",
        "suggestions": [
            {
                "label": "Open My Bookings",
                "description": "View and cancel your own bookings here.",
                "url": "/bookings/",
                "roles": ["student", "staff", "admin", "guest"],
            },
            {
                "label": "Admin Bookings",
                "description": "Admins manage any booking, including cancellations.",
                "url": "/admin/bookings",
                "roles": ["admin"],
            },
        ],
        "primary_link": {
            "label": "Go to My Bookings → /bookings/",
            "description": "Click here to view and cancel your bookings",
            "url": "/bookings/",
        },
    },
    {
        "keywords": ["book", "book a resource", "book resource", "reserve", "schedule", "how do i book"],
        "answer": "Pick a resource from the catalog, open its detail page, then use **Book this Resource** to confirm a slot.",
        "suggestions": [
            {
                "label": "Discover Resources",
                "description": "Browse the catalog; open a resource to view slots and book.",
                "url": "/resources/",
                "roles": ["guest", "student", "staff", "admin"],
            },
        ],
    },
    {
        "keywords": ["publish", "add resource", "create resource"],
        "answer": "Use these links to publish or edit a resource:",
        "suggestions": [
            {
                "label": "Add Resource",
                "description": "Create or update your own resource listing.",
                "url": "/resources/create",
                "roles": ["student", "staff"],
            },
            {
                "label": "Admin › Resources",
                "description": "Admins can add resources and assign owners.",
                "url": "/admin/resources",
                "roles": ["admin"],
            },
        ],
    },
    {
        "keywords": ["owner inbox", "owner messages", "approve booking"],
        "answer": "Open your owner tools here:",
        "suggestions": [
            {
                "label": "Owner Inbox & Messages",
                "description": "Approve requests and reply to user messages.",
                "url": "/resources/owner/requests",
                "roles": ["student", "staff", "admin"],
            },
        ],
    },
    {
        "keywords": ["admin inbox", "admin request", "book for me", "escalation"],
        "answer": "Handle admin requests from these pages:",
        "suggestions": [
            {
                "label": "Admin Inbox",
                "description": "See escalations & book-for-me conversations.",
                "url": "/admin/inbox",
                "roles": ["admin"],
            },
            {
                "label": "Admin Requests",
                "description": "Filter all open requests and approvals.",
                "url": "/admin/requests",
                "roles": ["admin"],
            },
        ],
    },
    {
        "keywords": ["book for user", "schedule for", "on behalf"],
        "answer": "To book on someone’s behalf:",
        "suggestions": [
            {
                "label": "Book Resource for a User",
                "description": "Admins schedule a resource for any student/staff member.",
                "url": "/admin/book-for-user",
                "roles": ["admin"],
            },
        ],
    },
]


def _load_docs() -> List[Dict[str, str]]:
    docs_path = _context_dir()
    docs: List[Dict[str, str]] = []
    if not docs_path.exists():
        return docs
    for path in sorted(docs_path.rglob("*.md")):
        try:
            docs.append({
                "name": path.name,
                "content": path.read_text(encoding="utf-8"),
            })
        except OSError:
            continue
    return docs


def _get_docs() -> List[Dict[str, str]]:
    global _DOC_CACHE
    if _DOC_CACHE is None:
        _DOC_CACHE = _load_docs()
    return _DOC_CACHE


def _current_roles() -> List[str]:
    roles: List[str] = []
    if getattr(current_user, "is_authenticated", False):
        roles.append("authenticated")
        if getattr(current_user, "is_admin", lambda: False)():
            roles.append("admin")
        if getattr(current_user, "is_staff", lambda: False)():
            roles.append("staff")
        if "admin" not in roles:
            roles.append("student")
    else:
        roles.append("guest")
    return roles


def _tokenize(query: str) -> List[str]:
    return [token for token in re.split(r"\W+", query.lower()) if len(token) >= 3]


def _score_text(text: str, tokens: List[str]) -> int:
    lowered = text.lower()
    return sum(lowered.count(token) for token in tokens)


def _build_snippet(content: str, tokens: List[str], window: int = 120) -> str:
    lowered = content.lower()
    for token in tokens:
        idx = lowered.find(token)
        if idx != -1:
            start = max(0, idx - window // 2)
            end = min(len(content), idx + window // 2)
            snippet = content[start:end].strip()
            if start > 0:
                snippet = "…" + snippet
            if end < len(content):
                snippet = snippet + "…"
            return snippet.replace("\n", " ")
    return content[:window].strip() + ("…" if len(content) > window else "")


def search_context_docs(query: str, top_n: int = 3) -> List[Dict[str, str]]:
    tokens = _tokenize(query)
    if not tokens:
        return []

    docs = _get_docs()
    scored = []
    for doc in docs:
        score = _score_text(doc["content"], tokens)
        if score:
            scored.append({
                "name": doc["name"],
                "score": score,
                "snippet": _build_snippet(doc["content"], tokens),
            })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_n]


def search_resources(query: str, limit: int = 5) -> List[Resource]:
    tokens = _tokenize(query)
    if not tokens:
        return []

    base_query = Resource.query.filter(Resource.status == Resource.STATUS_PUBLISHED)

    like_clauses = []
    for token in tokens:
        pattern = f"%{token}%"
        like_clauses.append(Resource.title.ilike(pattern))
        like_clauses.append(Resource.category.ilike(pattern))
        like_clauses.append(Resource.description.ilike(pattern))

    if like_clauses:
        base_query = base_query.filter(or_(*like_clauses))

    resources = base_query.limit(50).all()
    scored = []
    for res in resources:
        text = " ".join(filter(None, [res.title, res.category, res.description or ""]))
        score = _score_text(text, tokens)
        if score:
            scored.append((score, res))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [res for _, res in scored[:limit]]


def concierge_response(query: str) -> Dict[str, Any] | None:
    menu = _menu_response(query)
    if menu:
        return menu

    docs = search_context_docs(query)
    resources = search_resources(query)

    if not docs and not resources:
        return None

    suggestions: List[Dict[str, Any]] = []
    paragraphs: List[str] = []

    if docs:
        best_doc = docs[0]
        doc_text = _clean_markdown(best_doc["snippet"])
        paragraphs.append(doc_text)
        _infer_doc_shortcuts(doc_text, suggestions)

    if resources:
        for res in resources:
            suggestions.append({
                "label": res.title,
                "description": (res.description or "View details")[:90] + ("…" if res.description and len(res.description) > 90 else ""),
                "url": f"/resources/{res.id}",
            })
        if resources:
            paragraphs.append("I also found matching resources—use the cards below to jump into their detail pages.")

    answer = "\n\n".join(paragraphs)
    quick_replies = ["Book a resource", "Show menu", "Waitlist help"]
    if "My Bookings" in answer:
        quick_replies.insert(0, "Open My Bookings → /bookings/")

    response = {
        "answer": answer,
        "suggestions": suggestions,
        "quick_replies": quick_replies,
    }

    if suggestions:
        response["primary_link"] = suggestions[0]

    return response


def _menu_response(query: str) -> Optional[Dict[str, Any]]:
    text = query.lower()
    roles = _current_roles()
    for entry in MENU_SHORTCUTS:
        if not any(keyword in text for keyword in entry["keywords"]):
            continue
        options = [
            option for option in entry["suggestions"]
            if any(role in roles for role in option.get("roles", ["guest", "student", "staff", "admin"]))
        ]
        if not options:
            continue
        response = {
            "answer": entry["answer"],
            "suggestions": options,
            "quick_replies": entry.get("quick_replies", ["Show menu", "Need help", "Book a resource"]),
            "primary_link": entry.get("primary_link") or options[0],
        }
        return response
    return None


def _append_shortcut(suggestions: List[Dict[str, Any]], label: str, description: str, url: str):
    if any(item["url"] == url for item in suggestions):
        return
    suggestions.append({
        "label": label,
        "description": description,
        "url": url,
    })


def _infer_doc_shortcuts(doc_text: str, suggestions: List[Dict[str, Any]]):
    mapping = [
        ("/bookings/", "Open My Bookings", "Manage or cancel your own reservations.", "/bookings/"),
        ("/admin/bookings", "Admin Bookings", "Admins edit or cancel any booking.", "/admin/bookings"),
        ("/resources/create", "Add a Resource", "Publish or edit a listing you own.", "/resources/create"),
        ("/admin/resources", "Admin › Resources", "Admins publish resources and assign owners.", "/admin/resources"),
        ("/resources/owner/requests", "Owner Inbox & Messages", "Approve requests and chat with requesters.", "/resources/owner/requests"),
        ("/admin/inbox", "Admin Inbox", "Handle escalated book-for-me requests.", "/admin/inbox"),
    ]
    for token, label, desc, url in mapping:
        if token in doc_text:
            _append_shortcut(suggestions, label, desc, url)

