import os
import warnings

try:
    import importlib.metadata as std_metadata
except ImportError:  # pragma: no cover
    std_metadata = None

try:
    import importlib_metadata  # type: ignore
except ImportError:  # pragma: no cover
    importlib_metadata = None

try:
    from urllib3.exceptions import NotOpenSSLWarning
except ImportError:  # pragma: no cover
    NotOpenSSLWarning = None

if std_metadata and importlib_metadata:
    if not hasattr(std_metadata, "packages_distributions"):
        std_metadata.packages_distributions = importlib_metadata.packages_distributions  # type: ignore

if NotOpenSSLWarning:
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="google.api_core._python_version_support",
)

from flask import Flask, redirect, url_for
from flask_login import LoginManager
from datetime import datetime
from dotenv import load_dotenv
from src.models.models import db, User, Booking, BookingRequest, DowntimeBlock, Resource, Notification, SitePage
from src.controllers.auth_controller import auth_bp
from src.controllers.main_controller import main_bp
from src.controllers.booking_controller import booking_bp
from src.controllers.resource_controller import resource_bp
from src.controllers.assistant_controller import assistant_bp
from src.controllers.admin_controller import admin_bp  # NEW
from sqlalchemy import inspect, text


load_dotenv()
load_dotenv(".flaskenv")


def create_app():
    app = Flask(
        __name__,
        template_folder="src/views",
        static_folder="src/static"
    )

    app.config["SECRET_KEY"] = "supersecretkey"
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["GOOGLE_SEARCH_ENABLED"] = bool(
        os.getenv("GOOGLE_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    )

    db.init_app(app)

    with app.app_context():
        instance_path = os.path.join(basedir, "instance")
        os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, "app.db")
        db_existed = os.path.exists(db_path)

        # Always ensure all tables (including new ones) exist
        db.create_all()

        # Lightweight schema migration: ensure user status column exists
        inspector = inspect(db.engine)
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "status" not in user_columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
            db.session.commit()
            print("✅ Added 'status' column to users table.")

        message_columns = {column["name"] for column in inspector.get_columns("messages")}
        if "request_id" not in message_columns:
            db.session.execute(text("ALTER TABLE messages ADD COLUMN request_id INTEGER"))
            db.session.commit()
            print("✅ Added 'request_id' column to messages table.")

        booking_columns = {column["name"] for column in inspector.get_columns("bookings")}
        if "decision_at" not in booking_columns:
            db.session.execute(text("ALTER TABLE bookings ADD COLUMN decision_at DATETIME"))
            db.session.commit()
            print("✅ Added 'decision_at' column to bookings table.")
        if "booked_by_admin" not in booking_columns:
            db.session.execute(text("ALTER TABLE bookings ADD COLUMN booked_by_admin BOOLEAN DEFAULT 0"))
            db.session.commit()
            db.session.execute(text("UPDATE bookings SET booked_by_admin = 0 WHERE booked_by_admin IS NULL"))
            db.session.commit()
            print("✅ Added 'booked_by_admin' column to bookings table.")

        booking_request_columns = {column["name"] for column in inspector.get_columns("booking_requests")}
        if "kind" not in booking_request_columns:
            db.session.execute(text("ALTER TABLE booking_requests ADD COLUMN kind VARCHAR(20) DEFAULT 'allocator'"))
            db.session.commit()
            print("✅ Added 'kind' column to booking_requests table.")
        else:
            db.session.execute(text("UPDATE booking_requests SET kind = 'allocator' WHERE kind IS NULL"))
            db.session.commit()

        waitlist_columns = {column["name"] for column in inspector.get_columns("waitlist")}
        if "start_time" not in waitlist_columns:
            db.session.execute(text("ALTER TABLE waitlist ADD COLUMN start_time DATETIME"))
            db.session.commit()
            print("✅ Added 'start_time' column to waitlist table.")
        if "end_time" not in waitlist_columns:
            db.session.execute(text("ALTER TABLE waitlist ADD COLUMN end_time DATETIME"))
            db.session.commit()
            print("✅ Added 'end_time' column to waitlist table.")
        if "purpose" not in waitlist_columns:
            db.session.execute(text("ALTER TABLE waitlist ADD COLUMN purpose TEXT"))
            db.session.commit()
            print("✅ Added 'purpose' column to waitlist table.")
        if "status" not in waitlist_columns:
            db.session.execute(text("ALTER TABLE waitlist ADD COLUMN status VARCHAR(20) DEFAULT 'waiting'"))
            db.session.commit()
            db.session.execute(text("UPDATE waitlist SET status = 'waiting' WHERE status IS NULL"))
            db.session.commit()
            print("✅ Added 'status' column to waitlist table.")

        # Normalize resource lifecycle statuses
        resource_status_columns = {column["name"] for column in inspector.get_columns("resources")}
        if "status" in resource_status_columns:
            result = db.session.execute(text("SELECT DISTINCT status FROM resources")).fetchall()
            existing_statuses = {row[0] for row in result if row[0] is not None}
            if existing_statuses - {"draft", "published", "archived"}:
                db.session.execute(text("UPDATE resources SET status = 'published' WHERE status IN ('available', 'available ') OR status IS NULL"))
                db.session.execute(text("UPDATE resources SET status = 'archived' WHERE status = 'archived'"))
                db.session.execute(text("UPDATE resources SET status = 'draft' WHERE status IN ('unavailable', 'draft')"))
                db.session.commit()
                print("✅ Normalised resource lifecycle statuses.")

        def sync_booking_statuses():
            updated = False
            for booking in Booking.query.all():
                resource = booking.resource
                if not resource:
                    continue

                if resource.access_type == "public":
                    if booking.status != "approved":
                        booking.status = "approved"
                        if not booking.approved_by:
                            booking.approved_by = resource.owner_id
                        booking.decision_at = datetime.now()
                        updated = True
                else:
                    if booking.status == "approved" and not booking.approved_by:
                        booking.status = "pending"
                        updated = True

            if updated:
                db.session.commit()
                print("🔄 Booking statuses synchronised.")
            else:
                print("🔄 Booking statuses already up-to-date.")

        sync_booking_statuses()

        def ensure_site_pages():
            about_body = (
                "<p>Hoosier Hub connects IU students, staff, and administrators with campus resources. "
                "Browse spaces, submit bookings, and collaborate on scheduling in one streamlined experience.</p>"
            )
            contact_body = (
                "<p>Need help? Email <a href='mailto:hoosierhub@iu.edu'>hoosierhub@iu.edu</a>. "
                "Our support team typically replies within one business day.</p>"
            )
            defaults = {
                "about": {
                    "title": "About Hoosier Hub",
                    "body": about_body,
                },
                "contact": {
                    "title": "Contact Hoosier Hub",
                    "body": contact_body,
                },
            }
            created_or_updated = False
            for slug, data in defaults.items():
                page = SitePage.query.filter_by(slug=slug).first()
                if not page:
                    db.session.add(SitePage(slug=slug, title=data["title"], body=data["body"]))
                    created_or_updated = True
                elif slug == "contact" and "admin inbox" in page.body.lower():
                    page.body = contact_body
                    created_or_updated = True
            if created_or_updated:
                db.session.commit()

        ensure_site_pages()

        if not db_existed:
            print("✅ Database created successfully!")
            from src.data.seed_data import seed_database
            seed_database()
        else:
            print("✅ Database already exists (schema updated if needed)")

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        if user:
            user.unread_notifications = (
                Notification.query
                .filter_by(user_id=user.id, is_read=False)
                .order_by(Notification.created_at.desc())
                .all()
            )
        return user

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(admin_bp)  # NEW

    @app.context_processor
    def inject_owner_pending_count():
        from flask_login import current_user

        if not current_user.is_authenticated:
            return {"owner_pending_count": 0}

        pending_count = (
            BookingRequest.query
            .join(Resource, BookingRequest.resource_id == Resource.id)
            .filter(
                Resource.owner_id == current_user.id,
                BookingRequest.status == "pending",
                BookingRequest.kind == "owner",
            )
            .count()
        )
        return {"owner_pending_count": pending_count}

    @app.route("/")
    def home_redirect():
        from flask_login import current_user
        if hasattr(current_user, "is_authenticated") and current_user.is_authenticated:
            return redirect(url_for("resource_bp.list_resources"))
        return redirect(url_for("resource_bp.preview_resources"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)