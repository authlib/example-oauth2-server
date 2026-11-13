from urllib.parse import parse_qs
from urllib.parse import urlparse

from authlib.common.security import generate_token
from authlib.oauth2.rfc7636 import create_s256_code_challenge

from tests.utils import REDIRECT_URI
from tests.utils import authorize_url
from tests.utils import basic_auth
from tests.utils import bearer
from tests.utils import callback_params
from tests.utils import consent

CODE_VERIFIER = generate_token(48)


def code_url(client, **params):
    return authorize_url(
        **{
            "response_type": "code",
            "client_id": client["client_id"],
            "redirect_uri": REDIRECT_URI,
            "scope": "profile",
            "state": "xyz",
            "code_challenge": create_s256_code_challenge(CODE_VERIFIER),
            "code_challenge_method": "S256",
            **params,
        }
    )


def test_anonymous_user_is_sent_to_login(testapp, client):
    url = code_url(client)
    res = testapp.get(url)
    assert urlparse(res.location).path == "/"

    next_url = urlparse(parse_qs(urlparse(res.location).query)["next"][0])
    assert next_url.path == "/oauth/authorize"
    assert parse_qs(next_url.query) == parse_qs(urlparse(url).query)


def test_consent_page(logged_in, client, user):
    res = logged_in.get(code_url(client))
    assert "Test client" in res
    assert "profile" in res
    assert user["username"] in res


def test_authorization_code_flow(logged_in, client, user):
    params = callback_params(consent(logged_in, code_url(client)))
    assert params["state"] == "xyz"

    res = logged_in.post(
        "/oauth/token",
        {
            "grant_type": "authorization_code",
            "code": params["code"],
            "redirect_uri": REDIRECT_URI,
            "code_verifier": CODE_VERIFIER,
        },
        headers=basic_auth(client),
    )
    assert res.json["token_type"] == "Bearer"
    assert res.json["scope"] == "profile"
    assert res.json["refresh_token"]

    res = logged_in.get("/api/me", headers=bearer(res.json["access_token"]))
    assert res.json == {"id": user["id"], "username": user["username"]}


def test_consent_denied(logged_in, client):
    res = consent(logged_in, code_url(client), accept=False)
    params = callback_params(res)
    assert params["error"] == "access_denied"
    assert params["state"] == "xyz"


def test_authorization_code_is_single_use(logged_in, client):
    params = callback_params(consent(logged_in, code_url(client)))
    data = {
        "grant_type": "authorization_code",
        "code": params["code"],
        "redirect_uri": REDIRECT_URI,
        "code_verifier": CODE_VERIFIER,
    }
    logged_in.post("/oauth/token", data, headers=basic_auth(client))

    res = logged_in.post("/oauth/token", data, headers=basic_auth(client), status=400)
    assert res.json["error"] == "invalid_grant"


def test_pkce_is_optional_for_confidential_clients(logged_in, client):
    url = code_url(client, code_challenge=None, code_challenge_method=None)
    params = callback_params(consent(logged_in, url))

    res = logged_in.post(
        "/oauth/token",
        {
            "grant_type": "authorization_code",
            "code": params["code"],
            "redirect_uri": REDIRECT_URI,
        },
        headers=basic_auth(client),
    )
    assert res.json["access_token"]


def test_pkce_is_required_for_public_clients(logged_in, public_client):
    url = code_url(public_client, code_challenge=None, code_challenge_method=None)
    params = callback_params(logged_in.get(url))
    assert params["error"] == "invalid_request"
    assert params["state"] == "xyz"


def test_public_clients_must_send_the_code_verifier(logged_in, public_client):
    params = callback_params(consent(logged_in, code_url(public_client)))

    res = logged_in.post(
        "/oauth/token",
        {
            "grant_type": "authorization_code",
            "client_id": public_client["client_id"],
            "code": params["code"],
            "redirect_uri": REDIRECT_URI,
        },
        status=400,
    )
    assert res.json["error"] == "invalid_request"


def test_wrong_code_verifier(logged_in, client):
    params = callback_params(consent(logged_in, code_url(client)))
    res = logged_in.post(
        "/oauth/token",
        {
            "grant_type": "authorization_code",
            "code": params["code"],
            "redirect_uri": REDIRECT_URI,
            "code_verifier": generate_token(48),
        },
        headers=basic_auth(client),
        status=400,
    )
    assert res.json["error"] == "invalid_grant"


def test_unknown_client(logged_in):
    res = logged_in.get(code_url({"client_id": "unknown"}), status=400)
    assert "invalid_client" in res
