import base64
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse

REDIRECT_URI = "http://client.test/callback"


def basic_auth(client):
    credentials = f"{client['client_id']}:{client['client_secret']}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def bearer(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def authorize_url(**params):
    """Build an authorization URL. Parameters set to None are left out."""
    query = {key: value for key, value in params.items() if value is not None}
    return "/oauth/authorize?" + urlencode(query)


def consent(testapp, url, *, accept=True):
    """Open the consent page and submit the form."""
    form = testapp.get(url).forms[0]
    form["confirm"].checked = accept
    return form.submit()


def callback_params(res, *, fragment=False):
    """Return the parameters of a redirection to the client."""
    assert res.location.startswith(REDIRECT_URI)
    url = urlparse(res.location)
    query = url.fragment if fragment else url.query
    return {key: values[0] for key, values in parse_qs(query).items()}


def password_token(testapp, client, user, *, status=200, **params):
    """Request a token with the password grant."""
    return testapp.post(
        "/oauth/token",
        {
            "grant_type": "password",
            "username": user["username"],
            "password": "valid",
            "scope": "profile",
            **params,
        },
        headers=basic_auth(client),
        status=status,
    )
