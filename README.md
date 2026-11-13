# Example of OAuth 2.0 server

An example of OAuth 2.0 authorization server built with [Authlib](https://authlib.org/) and Flask.
Read its code to learn how to build a server.

This page explains how to run the example.
It assumes basic knowledge of OAuth 2.0.
The [Authlib documentation](https://docs.authlib.org/en/latest/oauth2/authorization-server/flask/) explains how to build a server.
For a ready-to-use server to test an OAuth 2.0 client, see [Auth Server Playground](https://github.com/authlib/auth-server-playground).

## Features

The server supports these grants and endpoints:

- Authorization code grant, with PKCE (RFC 7636). Public clients must use PKCE.
- Implicit grant.
- Resource owner password credentials grant.
- Client credentials grant.
- Refresh token grant.
- Token revocation (RFC 7009).
- A protected resource, `/api/me`, that needs the `profile` scope.

## Run the server

Run the server with [uv](https://docs.astral.sh/uv/):

```bash
uv run flask --app website run
```

The server listens on `http://127.0.0.1:5000`.
It stores its data in a SQLite database in the Flask instance folder.

## Try the password grant

Open `http://127.0.0.1:5000/` and log in with any user name.
The server creates the user at the first login.
The password of every user is `valid`.

Then create a client:

1. Click **Create Client**.
2. Set **Allowed Scope** to `profile`.
3. Set **Allowed Grant Types** to `password`.
4. Keep `client_secret_basic` as the token endpoint authentication method.
5. Submit the form. The home page shows the `client_id` and `client_secret` of the new client.

Request a token with the password grant:

```bash
curl -u ${client_id}:${client_secret} -X POST http://127.0.0.1:5000/oauth/token \
    -d grant_type=password -d username=${username} -d password=valid -d scope=profile
```

The server returns a token:

```json
{"access_token": "UGnmW1AnVJPWu9mLCbZwiWHHgW28An7Qq2uzBo5uQz", "expires_in": 864000, "refresh_token": "Z0kS5WFkCGUOGZZEoK9fFUXIxXGI4HiOKJzZ336KJlUKc4Hy", "scope": "profile", "token_type": "Bearer"}
```

Call the protected resource with the access token:

```bash
curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:5000/api/me
```

```json
{"id":1,"username":"alice"}
```

The other endpoints are `/oauth/authorize` and `/oauth/revoke`.
Grant types and redirect URIs go one per line in the client form.

## Development

Run the tests:

```bash
uv run pytest
```

Install the Git hooks that check the code style and the commit messages:

```bash
uv run prek install
```

## License

The server is distributed under the BSD 3-Clause license. See [LICENSE](LICENSE).
