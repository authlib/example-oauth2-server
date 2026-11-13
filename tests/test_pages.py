import pytest

from authlib_server_demo.models import OAuth2Client
from authlib_server_demo.models import User


def test_home_shows_the_login_form(testapp):
    res = testapp.get("/")
    assert res.forms[0]["username"]


def test_login_creates_the_user(app, testapp):
    res = testapp.post("/", {"username": "bob"})
    assert res.location.endswith("/")

    res = res.follow()
    assert "Logged in as" in res
    assert "bob" in res
    with app.app_context():
        assert User.query.filter_by(username="bob").count() == 1


def test_login_with_an_existing_user(app, testapp, user):
    testapp.post("/", {"username": user["username"]})
    with app.app_context():
        assert User.query.filter_by(username=user["username"]).count() == 1


def test_login_redirects_to_next(testapp):
    res = testapp.post("/?next=/create_client", {"username": "bob"})
    assert res.location.endswith("/create_client")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="home() redirects to any 'next' URL",
)
def test_login_ignores_an_external_next(testapp):
    res = testapp.post("/?next=https://evil.test/", {"username": "bob"})
    assert not res.location.startswith("https://evil.test")


def test_logout(logged_in):
    res = logged_in.get("/logout")
    assert res.location.endswith("/")
    assert "Logged in as" not in res.follow()


def test_create_client_needs_a_user(testapp):
    res = testapp.get("/create_client")
    assert res.location.endswith("/")


def _fill_client_form(form, auth_method):
    form["client_name"] = "My client"
    form["client_uri"] = "http://client.test"
    form["scope"] = "profile"
    form["redirect_uri"] = "http://client.test/callback\nhttp://client.test/other"
    form["grant_type"] = "authorization_code\nrefresh_token"
    form["response_type"] = "code"
    form["token_endpoint_auth_method"] = auth_method


def test_create_confidential_client(app, logged_in, user):
    form = logged_in.get("/create_client").forms[0]
    _fill_client_form(form, "client_secret_basic")
    res = form.submit()
    assert res.location.endswith("/")

    with app.app_context():
        client = OAuth2Client.query.one()
        assert client.user_id == user["id"]
        assert client.client_secret
        assert client.client_name == "My client"
        assert client.redirect_uris == [
            "http://client.test/callback",
            "http://client.test/other",
        ]
        assert client.grant_types == ["authorization_code", "refresh_token"]
        assert client.token_endpoint_auth_method == "client_secret_basic"

    assert "My client" in res.follow()


def test_create_public_client(app, logged_in):
    form = logged_in.get("/create_client").forms[0]
    _fill_client_form(form, "none")
    form.submit()

    with app.app_context():
        client = OAuth2Client.query.one()
        assert client.client_secret == ""
        assert client.token_endpoint_auth_method == "none"
