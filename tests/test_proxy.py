from urllib.parse import parse_qs
from urllib.parse import urlsplit

import pytest

from authlib_server_demo import is_proxy_fix_enabled
from tests.utils import basic_auth


def client_credentials(testapp, client, headers):
    return testapp.post(
        "/oauth/token",
        {"grant_type": "client_credentials"},
        headers={**basic_auth(client), **headers},
        extra_environ={"HTTP_HOST": "server.test"},
        expect_errors=True,
    )


@pytest.mark.parametrize("insecure_transport", [False])
def test_plain_http_is_refused(testapp, client):
    res = client_credentials(testapp, client, {})
    assert res.status_int == 400
    assert res.json["error"] == "insecure_transport"


@pytest.mark.parametrize("insecure_transport", [False])
def test_forwarded_proto_is_ignored_by_default(testapp, client):
    res = client_credentials(testapp, client, {"X-Forwarded-Proto": "https"})
    assert res.json["error"] == "insecure_transport"


@pytest.mark.parametrize("insecure_transport", [False])
@pytest.mark.parametrize("proxy_fix", [True])
def test_forwarded_proto_is_used_behind_a_proxy(testapp, client):
    res = client_credentials(testapp, client, {"X-Forwarded-Proto": "https"})
    assert res.status_int == 200
    assert res.json["access_token"]


def login_next(res):
    return parse_qs(urlsplit(res.location).query)["next"][0]


def test_forwarded_prefix_is_ignored_by_default(testapp):
    res = testapp.get("/oauth/authorize", headers={"X-Forwarded-Prefix": "/auth"})
    assert login_next(res) == "/oauth/authorize?"


@pytest.mark.parametrize("proxy_fix", [True])
def test_forwarded_prefix_is_used_behind_a_proxy(testapp):
    res = testapp.get("/oauth/authorize", headers={"X-Forwarded-Prefix": "/auth"})
    assert urlsplit(res.location).path == "/auth/"
    assert login_next(res) == "/auth/oauth/authorize?"


@pytest.mark.parametrize(
    "value,enabled",
    [
        (None, False),
        ("", False),
        ("0", False),
        ("false", False),
        ("False", False),
        ("1", True),
        ("true", True),
        (" TRUE ", True),
    ],
)
def test_proxy_fix_values(monkeypatch, value, enabled):
    if value is None:
        monkeypatch.delenv("PROXY_FIX", raising=False)
    else:
        monkeypatch.setenv("PROXY_FIX", value)
    assert is_proxy_fix_enabled() is enabled


def test_proxy_fix_invalid_value(monkeypatch):
    monkeypatch.setenv("PROXY_FIX", "yes")
    with pytest.raises(ValueError, match="PROXY_FIX"):
        is_proxy_fix_enabled()


@pytest.mark.parametrize("proxy_fix", [True])
def test_logout_stays_under_the_prefix(testapp):
    res = testapp.get("/logout", headers={"X-Forwarded-Prefix": "/auth"})
    assert urlsplit(res.location).path == "/auth/"
