"""Pytest configuration."""

import sys
from pathlib import Path

import pytest

from app import create_app
from src.models.models import db

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def app(tmp_path):
    app = create_app()
    test_db = tmp_path / "test_app.db"
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{test_db}",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="testserver",
    )
    with app.app_context():
        db.engine.dispose()
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

