import time

from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from flask import Blueprint
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import gen_salt

from .models import OAuth2Client
from .models import User
from .models import db
from .oauth2 import authorization
from .oauth2 import require_oauth

bp = Blueprint("home", __name__)


def current_user():
    if "id" not in session:
        return None
    return db.session.get(User, session["id"])


def is_local_path(url):
    """Tell whether the URL is a path on this server, and not another site."""
    if not url.isprintable() or "\\" in url:
        return False
    return url.startswith("/") and not url.startswith("//")


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


@bp.route("/", methods=("GET", "POST"))
def home():
    if request.method == "POST":
        username = request.form.get("username")
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session["id"] = user.id
        next_page = request.args.get("next")
        if next_page and is_local_path(next_page):
            return redirect(next_page)
        return redirect(url_for("home.home"))
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []

    return render_template("home.html", user=user, clients=clients)


@bp.route("/logout")
def logout():
    session.pop("id", None)
    return redirect(url_for("home.home"))


@bp.route("/create_client", methods=("GET", "POST"))
def create_client():
    user = current_user()
    if not user:
        return redirect(url_for("home.home"))
    if request.method == "GET":
        return render_template("create_client.html")

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )

    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"],
    }
    client.set_client_metadata(client_metadata)

    if form["token_endpoint_auth_method"] == "none":
        client.client_secret = ""
    else:
        client.client_secret = gen_salt(48)

    db.session.add(client)
    db.session.commit()
    return redirect(url_for("home.home"))


@bp.route("/oauth/authorize", methods=["GET", "POST"])
def authorize():
    user = current_user()
    if not user:
        return redirect(
            url_for("home.home", next=request.script_root + request.full_path)
        )

    try:
        grant = authorization.get_consent_grant(end_user=user)
    except OAuth2Error as error:
        return authorization.handle_error_response(request, error)

    if request.method == "GET":
        return render_template("authorize.html", user=user, grant=grant)

    grant_user = user if "confirm" in request.form else None
    return authorization.create_authorization_response(
        grant=grant, grant_user=grant_user
    )


@bp.route("/oauth/token", methods=["POST"])
def issue_token():
    return authorization.create_token_response()


@bp.route("/oauth/revoke", methods=["POST"])
def revoke_token():
    return authorization.create_endpoint_response("revocation")


@bp.route("/api/me")
@require_oauth("profile")
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)
