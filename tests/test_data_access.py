from datetime import datetime, timedelta, timezone

from src.models.models import db, User, Resource, Booking
from src.data_access import resources_dal, bookings_dal


def _create_user(name: str, email: str, role: str = "staff"):
    user = User(name=name, email=email, role=role)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


def test_resources_dal_crud(app):
    with app.app_context():
        owner = _create_user("Dr. Owner", "owner@faculty.iu.edu", "staff")

        resource = Resource(
            title="GPU Lab",
            description="NVIDIA A100 cluster.",
            category="Lab",
            capacity=2,
            location="Luddy Hall B201",
            access_type="restricted",
            owner_id=owner.id,
            status=Resource.STATUS_PUBLISHED,
        )
        db.session.add(resource)
        db.session.commit()

        fetched = resources_dal.get_resource_or_404(resource.id)
        assert fetched.title == "GPU Lab"

        mine = resources_dal.list_resources_for_owner(owner.id)
        assert resource in mine

        published = resources_dal.list_published_resources()
        assert resource in published


def test_bookings_dal_lists(app):
    with app.app_context():
        owner = _create_user("Owner", "staff@faculty.iu.edu", "staff")
        student = _create_user("Student", "student@iu.edu", "student")

        resource = Resource(
            title="Quiet Room",
            category="Study Room",
            capacity=1,
            location="Wells Library",
            access_type="public",
            owner_id=owner.id,
            status=Resource.STATUS_PUBLISHED,
        )
        db.session.add(resource)
        db.session.commit()

        booking = Booking(
            resource_id=resource.id,
            user_id=student.id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=2),
            purpose="Midterm prep",
            status="approved",
        )
        db.session.add(booking)
        db.session.commit()

        all_bookings = bookings_dal.list_all_bookings()
        assert booking in all_bookings

        user_bookings = bookings_dal.list_bookings_for_user(student.id)
        assert booking in user_bookings

