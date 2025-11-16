from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
import bcrypt

# Initialize SQLAlchemy
db = SQLAlchemy()

# Association table for favorite resources
resource_favorites = db.Table(
    "resource_favorites",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("resource_id", db.Integer, db.ForeignKey("resources.id"), primary_key=True)
)


# --------------------------------------------------
# USER MODEL
# --------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="student")  # student, staff, admin
    status = db.Column(db.String(20), default="active", nullable=False)  # active, inactive
    department = db.Column(db.String(100))
    profile_image = db.Column(db.String(255), default="https://ui-avatars.com/api/?background=990000&color=fff&name=User")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships - FIXED with foreign_keys
    resources = db.relationship("Resource", backref="owner", lazy=True, foreign_keys="Resource.owner_id")
    bookings = db.relationship("Booking", backref="user", lazy=True, foreign_keys="Booking.user_id")
    reviews = db.relationship("Review", backref="reviewer", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)
    favorite_resources = db.relationship(
        "Resource",
        secondary=resource_favorites,
        back_populates="favorited_by"
    )
    waitlist_entries = db.relationship("Waitlist", backref="user", lazy=True)

    # Password handling
    def set_password(self, password):
        """Hash and set user password securely."""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        """Verify user password."""
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    # Role helpers
    def is_admin(self):
        return self.role == "admin"

    def is_staff(self):
        return self.role == "staff"

    def is_student(self):
        return self.role == "student"

    @property
    def is_active(self):
        """Override Flask-Login active flag based on status."""
        return self.status == "active"

    def __repr__(self):
        return f"<User {self.email}>"


# --------------------------------------------------
# RESOURCE MODEL
# --------------------------------------------------
class Resource(db.Model):
    __tablename__ = "resources"

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # Study Room, Lab, Equipment, Tutoring
    capacity = db.Column(db.Integer, default=1)
    location = db.Column(db.String(200))
    image_url = db.Column(db.String(500), default="https://picsum.photos/400/300")
    
    # Access control
    access_type = db.Column(db.String(20), default="public")  # public or restricted
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Availability
    available_slots = db.Column(db.Integer, default=10)  # Total slots available
    status = db.Column(db.String(20), default=STATUS_DRAFT)  # draft, published, archived
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    bookings = db.relationship("Booking", backref="resource", lazy=True, cascade="all, delete-orphan", foreign_keys="Booking.resource_id")
    reviews = db.relationship("Review", backref="resource", lazy=True, cascade="all, delete-orphan")
    waitlist_entries = db.relationship("Waitlist", backref="resource", lazy=True, cascade="all, delete-orphan")
    booking_requests = db.relationship(
        "BookingRequest",
        back_populates="resource",
        lazy=True,
        cascade="all, delete-orphan"
    )
    favorited_by = db.relationship(
        "User",
        secondary=resource_favorites,
        back_populates="favorite_resources"
    )

    def get_available_slots(self, start_time=None, end_time=None, exclude_booking_id=None):
        """Calculate remaining slots, optionally for a specific time window."""
        def normalize(dt):
            if not dt:
                return None
            if dt.tzinfo:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        statuses = ["pending", "approved"]
        query = Booking.query.filter(
            Booking.resource_id == self.id,
            Booking.status.in_(statuses)
        )
        if exclude_booking_id is not None:
            query = query.filter(Booking.id != exclude_booking_id)

        if start_time and end_time:
            start_norm = normalize(start_time)
            end_norm = normalize(end_time)
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            start_norm = now
            end_norm = now

        # Check downtime blocks
        downtime_query = DowntimeBlock.query.filter_by(resource_id=self.id)
        if start_norm and end_norm:
            downtime_query = downtime_query.filter(
                DowntimeBlock.start_time < end_norm,
                DowntimeBlock.end_time > start_norm
            )

        if downtime_query.first():
            return 0

        if start_norm and end_norm:
            query = query.filter(
                Booking.start_time < end_norm,
                Booking.end_time > start_norm
            )

        overlap_count = query.count()
        return max(0, self.capacity - overlap_count)

    def average_rating(self):
        """Calculate average rating from reviews."""
        reviews = Review.query.filter_by(resource_id=self.id).all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def is_published(self):
        return self.status == self.STATUS_PUBLISHED

    @property
    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    @property
    def is_archived(self):
        return self.status == self.STATUS_ARCHIVED

    def __repr__(self):
        return f"<Resource {self.title}>"


# --------------------------------------------------
# BOOKING MODEL
# --------------------------------------------------
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.Text)  # Why they need it
    
    booked_by_admin = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected, cancelled, completed
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"))  # Staff/Admin who approved
    rejection_reason = db.Column(db.Text)
    decision_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships - FIXED with foreign_keys
    approver = db.relationship("User", foreign_keys=[approved_by], backref="approved_bookings")

    def __repr__(self):
        return f"<Booking Resource={self.resource_id} User={self.user_id} Status={self.status}>"


# --------------------------------------------------
# RESOURCE DOWNTIME BLOCKS
# --------------------------------------------------
class DowntimeBlock(db.Model):
    __tablename__ = "downtime_blocks"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    resource = db.relationship("Resource", backref=db.backref("downtime_blocks", lazy=True, cascade="all, delete-orphan"))
    creator = db.relationship("User", backref="created_downtimes")

    def overlaps(self, start, end):
        return self.start_time < end and self.end_time > start

    def __repr__(self):
        return f"<Downtime Resource={self.resource_id} {self.start_time}→{self.end_time}>"


# --------------------------------------------------
# BOOKING REQUEST MODEL
# --------------------------------------------------
class BookingRequest(db.Model):
    __tablename__ = "booking_requests"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"))

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.Text)
    note = db.Column(db.Text)

    status = db.Column(db.String(20), default="pending", nullable=False)  # pending, approved, denied, closed
    decision_note = db.Column(db.Text)
    decided_at = db.Column(db.DateTime)
    kind = db.Column(db.String(20), default="allocator", nullable=False)  # allocator, owner

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    requester = db.relationship("User", foreign_keys=[requester_id], backref="submitted_booking_requests")
    resource = db.relationship("Resource", back_populates="booking_requests", lazy=True)
    booking = db.relationship("Booking", foreign_keys=[booking_id], backref=db.backref("request", uselist=False))

    def mark(self, status, note=None):
        self.status = status
        self.decision_note = note
        self.decided_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<BookingRequest Resource={self.resource_id} Requester={self.requester_id} Status={self.status}>"


# --------------------------------------------------
# REVIEW MODEL
# --------------------------------------------------
class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"))
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Review Resource={self.resource_id} Rating={self.rating}>"


# --------------------------------------------------
# NOTIFICATION MODEL
# --------------------------------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # booking_approved, booking_rejected, waitlist_available, etc.
    
    is_read = db.Column(db.Boolean, default=False)
    related_url = db.Column(db.String(255))  # Link to related page
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Notification User={self.user_id} Type={self.notification_type}>"


# --------------------------------------------------
# EMAIL LOG MODEL
# --------------------------------------------------
class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<EmailLog to={self.recipient_email}>"


# --------------------------------------------------
# WAITLIST MODEL
# --------------------------------------------------
class Waitlist(db.Model):
    __tablename__ = "waitlist"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default="waiting")
    
    position = db.Column(db.Integer)  # Position in queue
    notified = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Waitlist Resource={self.resource_id} User={self.user_id} Position={self.position}>"


# --------------------------------------------------
# MESSAGE MODEL (for user-to-user communication)
# --------------------------------------------------
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"))  # Related booking if any
    request_id = db.Column(db.Integer, db.ForeignKey("booking_requests.id"))  # Related booking request if any
    
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships - FIXED with foreign_keys
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    request = db.relationship(
        "BookingRequest",
        foreign_keys=[request_id],
        backref=db.backref("messages", cascade="all, delete-orphan", lazy=True)
    )

    def __repr__(self):
        return f"<Message From={self.sender_id} To={self.receiver_id}>"


# --------------------------------------------------
# RESOURCE CONVERSATIONS
# --------------------------------------------------
class ResourceConversation(db.Model):
    __tablename__ = "resource_conversations"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    resource = db.relationship("Resource", backref=db.backref("conversations", cascade="all, delete-orphan"))
    owner = db.relationship("User", foreign_keys=[owner_id], backref="owned_conversations")
    requester = db.relationship("User", foreign_keys=[requester_id], backref="requested_conversations")


class ResourceConversationMessage(db.Model):
    __tablename__ = "resource_conversation_messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("resource_conversations.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = db.relationship(
        "ResourceConversation",
        backref=db.backref("messages", cascade="all, delete-orphan", order_by="ResourceConversationMessage.created_at")
    )
    sender = db.relationship("User")


class SitePage(db.Model):
    __tablename__ = "site_pages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    editor = db.relationship("User", foreign_keys=[updated_by])