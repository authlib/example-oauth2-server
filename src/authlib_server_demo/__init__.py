import os

from flask import Flask

from .models import db
from .oauth2 import config_oauth
from .routes import bp


def create_app(config=None):
    """Create the Flask application, configured from the environment."""
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///db.sqlite"
    )
    app.config["OAUTH2_REFRESH_TOKEN_GENERATOR"] = True
    # Browsers do not send the session cookie with cross-site POST requests,
    # such as a forged consent form.
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if config:
        app.config.update(config)

    setup_app(app)
    return app


def setup_app(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
    config_oauth(app)
    app.register_blueprint(bp)
