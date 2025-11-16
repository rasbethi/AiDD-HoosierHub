from datetime import datetime, timezone

from typing import Optional

from src.models.models import db, Notification, EmailLog, User


def send_notification(user: User, title: str, message: str, notification_type: str, related_url: Optional[str] = None):
    """Create an in-app notification and log a simulated email."""
    if user is None:
        return None

    notification = Notification(
        user_id=user.id,
        title=title,
        message=message,
        notification_type=notification_type,
        related_url=related_url,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(notification)

    email_log = EmailLog(
        recipient_email=user.email,
        subject=title,
        body=message,
        sent_at=datetime.now(timezone.utc),
    )
    db.session.add(email_log)

    return notification

