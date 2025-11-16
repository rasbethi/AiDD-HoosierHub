# pyright: reportMissingImports=false

from flask import Blueprint, render_template, abort
from flask_login import current_user
from sqlalchemy import func

from src.models.models import Resource, Review, SitePage

main_bp = Blueprint("main", __name__)


@main_bp.route("/home")
def home():
    featured_resources = (
        Resource.query
        .filter(Resource.status == Resource.STATUS_PUBLISHED)
        .order_by(Resource.created_at.desc())
        .limit(3)
        .all()
    )

    review_samples = (
        Review.query
        .filter(Review.comment.isnot(None))
        .order_by(Review.created_at.desc())
        .limit(6)
        .all()
    )
    return render_template("preview.html", featured=featured_resources, review_samples=review_samples, user=current_user)


def _load_page(slug: str) -> SitePage:
    page = SitePage.query.filter_by(slug=slug).first()
    if not page:
        abort(404)
    return page


@main_bp.route("/about")
def about_page():
    page = _load_page("about")
    return render_template("pages/page.html", page=page)


@main_bp.route("/contact")
def contact_page():
    page = _load_page("contact")
    return render_template("pages/page.html", page=page)
