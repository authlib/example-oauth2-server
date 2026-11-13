import pytest

from website import create_app
from website.models import db


@pytest.fixture
def make_app():
    """Create applications, and close their database at the end of the test."""
    apps = []

    def make():
        app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://"})
        apps.append(app)
        return app

    yield make

    for app in apps:
        with app.app_context():
            db.engine.dispose()


def test_secret_key_from_the_environment(monkeypatch, make_app):
    monkeypatch.setenv("SECRET_KEY", "from-env")
    assert make_app().config["SECRET_KEY"] == "from-env"


def test_random_secret_key_without_environment(monkeypatch, make_app):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    first = make_app()
    second = make_app()
    assert first.config["SECRET_KEY"]
    assert first.config["SECRET_KEY"] != second.config["SECRET_KEY"]
