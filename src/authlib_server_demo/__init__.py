import os
import secrets

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .models import db
from .oauth2 import config_oauth
from .routes import bp


def is_proxy_fix_enabled():
    """Read from the environment whether the application runs behind a proxy."""
    value = os.environ.get("PROXY_FIX", "").strip().lower()
    if value in ("", "0", "false"):
        return False
    if value in ("1", "true"):
        return True
    raise ValueError(f"PROXY_FIX must be true or false, got {value!r}")


def create_app(config=None):
    """Create the Flask application, configured from the environment."""
    app = Flask(__name__)

    # Without SECRET_KEY, a random key is used, and the sessions do not
    # survive a restart.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex()
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///db.sqlite"
    )
    app.config["OAUTH2_REFRESH_TOKEN_GENERATOR"] = True
    # Browsers do not send the session cookie with cross-site POST requests,
    # such as a forged consent form.
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if config:
        app.config.update(config)

    if is_proxy_fix_enabled():
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_prefix=1)

    setup_app(app)
    return app


def setup_app(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
    config_oauth(app)
    app.register_blueprint(bp)
