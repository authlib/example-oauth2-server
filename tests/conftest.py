import time

import pytest
from flask_webtest import TestApp

from authlib_server_demo import create_app
from authlib_server_demo.models import OAuth2Client
from authlib_server_demo.models import User
from authlib_server_demo.models import db
from tests.utils import REDIRECT_URI


@pytest.fixture
def proxy_fix():
    """Return whether the application runs behind a reverse proxy."""
    return False


@pytest.fixture
def insecure_transport():
    """Return whether Authlib accepts plain HTTP requests."""
    return True


@pytest.fixture
def app(monkeypatch, proxy_fix, insecure_transport):
    monkeypatch.setenv("PROXY_FIX", str(proxy_fix))
    if insecure_transport:
        monkeypatch.setenv("AUTHLIB_INSECURE_TRANSPORT", "1")
    else:
        monkeypatch.delenv("AUTHLIB_INSECURE_TRANSPORT", raising=False)

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    yield app

    with app.app_context():
        db.engine.dispose()


@pytest.fixture
def testapp(app):
    return TestApp(app)


@pytest.fixture
def user(app):
    with app.app_context():
        user = User(username="alice")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "username": user.username}


@pytest.fixture
def logged_in(testapp, user):
    """Log the user in the test application session."""
    testapp.post("/", {"username": user["username"]})
    return testapp


def make_client(app, user, *, client_id, client_secret, metadata):
    with app.app_context():
        client = OAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            client_id_issued_at=int(time.time()),
            user_id=user["id"],
        )
        client.set_client_metadata(
            {
                "client_name": "Test client",
                "redirect_uris": [REDIRECT_URI],
                "scope": "profile",
                **metadata,
            }
        )
        db.session.add(client)
        db.session.commit()
    return {"client_id": client_id, "client_secret": client_secret}


@pytest.fixture
def client(app, user):
    """Confidential client for every grant except the implicit one."""
    return make_client(
        app,
        user,
        client_id="confidential-client",
        client_secret="confidential-secret",
        metadata={
            "grant_types": [
                "authorization_code",
                "password",
                "client_credentials",
                "refresh_token",
            ],
            "response_types": ["code"],
            "token_endpoint_auth_method": "client_secret_basic",
        },
    )


@pytest.fixture
def public_client(app, user):
    """Public client, without a secret."""
    return make_client(
        app,
        user,
        client_id="public-client",
        client_secret="",
        metadata={
            "grant_types": ["authorization_code", "implicit"],
            "response_types": ["code", "token"],
            "token_endpoint_auth_method": "none",
        },
    )
