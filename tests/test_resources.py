from authlib_server_demo.models import OAuth2Client
from authlib_server_demo.models import db
from tests.utils import basic_auth
from tests.utils import bearer
from tests.utils import password_token


def test_api_me_needs_a_token(testapp):
    res = testapp.get("/api/me", status=401)
    assert res.headers["WWW-Authenticate"] == "Bearer"


def test_api_me_rejects_an_unknown_token(testapp):
    res = testapp.get("/api/me", headers=bearer("unknown"), status=401)
    assert res.json["error"] == "invalid_token"


def test_api_me_needs_the_profile_scope(app, testapp, client, user):
    with app.app_context():
        db_client = OAuth2Client.query.filter_by(client_id=client["client_id"]).one()
        db_client.set_client_metadata({**db_client.client_metadata, "scope": "email"})
        db.session.commit()

    token = password_token(testapp, client, user, scope="email").json
    res = testapp.get("/api/me", headers=bearer(token["access_token"]), status=403)
    assert res.json["error"] == "insufficient_scope"


def test_revocation(testapp, client, user):
    token = password_token(testapp, client, user).json
    testapp.get("/api/me", headers=bearer(token["access_token"]))

    testapp.post(
        "/oauth/revoke",
        {"token": token["access_token"], "token_type_hint": "access_token"},
        headers=basic_auth(client),
    )

    testapp.get("/api/me", headers=bearer(token["access_token"]), status=401)
