# Authlib server demo

An OAuth 2.0 authorization server built with [Authlib](https://authlib.org/).
Run it to test and debug an OAuth 2.0 client, or deploy it to try the server features of Authlib.

This page explains how to run and configure the server.
It assumes basic knowledge of OAuth 2.0.
To build a server with Authlib, read the [Authlib documentation](https://docs.authlib.org/).

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

Run the server from the source code with [uv](https://docs.astral.sh/uv/):

```bash
uv run authlib-server-demo
```

The server listens on `http://127.0.0.1:5000`.
It stores its data in a SQLite database in the Flask instance folder.

Run the server with Docker:

```bash
docker build -t authlib-server-demo .
docker run -p 5000:5000 -v authlib-server-demo:/data authlib-server-demo
```

The container stores the database in `/data`.
The volume keeps the data when the container is removed.

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

## Configuration

The server reads its configuration from environment variables.
It also loads a `.env` file from the current directory.
`example.env` lists the variables:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | random | Key that signs the session cookies. Without it, sessions end when the server restarts. |
| `DATABASE_URL` | `sqlite:///db.sqlite` | SQLAlchemy database URL. In the Docker image, `sqlite:////data/db.sqlite`. |
| `FLASK_RUN_HOST` | `127.0.0.1` | Address the server listens on. In the Docker image, `0.0.0.0`. |
| `FLASK_RUN_PORT` | `5000` | Port the server listens on. |
| `FLASK_DEBUG` | `False` | Set to `True` to enable the Flask debug mode. |
| `PROXY_FIX` | `false` | Set to `true` behind a reverse proxy. |
| `AUTHLIB_INSECURE_TRANSPORT` | unset | Set to `1` to accept plain HTTP requests. |

Per RFC 6749 §3.1 and §3.2, the OAuth 2.0 endpoints require TLS.
The server accepts plain HTTP on `localhost` and `127.0.0.1`.
On other hosts, plain HTTP requests get an `insecure_transport` error, unless `AUTHLIB_INSECURE_TRANSPORT` is set.
Never set it in production.

## Run behind a reverse proxy

Behind a reverse proxy or a load balancer, enable the proxy support:

```bash
export PROXY_FIX=true
```

The server then trusts the `X-Forwarded-Proto` and `X-Forwarded-Prefix` headers set by the closest proxy.
When the proxy handles TLS, the server sees HTTPS requests and accepts them.
Under a sub-path, the redirections start with the path prefix.
The server also trusts `X-Forwarded-For`, which only changes the client address in the logs.
Only enable it when a proxy is present.
Without a proxy, clients could forge these headers.

The proxy must set `X-Forwarded-Proto` and forward the original `Host` header.
It must also set `X-Forwarded-Prefix`, or clear it when the server is at the root of the domain.
Otherwise clients could send their own prefix.
With nginx, at the root of the domain:

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix "";
}
```

Under a sub-path, the proxy removes the prefix from the request path and sends it in `X-Forwarded-Prefix`:

```nginx
location /auth/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /auth;
}
```

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
