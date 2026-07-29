import base64
import hashlib
import hmac
import json
import os
import sys
import time

from flask import Blueprint, current_app, jsonify, request

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.models import authenticate_user, create_user, get_user_by_username

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
TOKEN_EXPIRY_HOURS = 24


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _create_token(payload: dict, secret: str) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url(json.dumps(payload).encode())
    sig_input = f"{header}.{body}".encode()
    sig = _b64url(hmac.new(secret.encode(), sig_input, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def _verify_token(token: str, secret: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        sig_input = f"{header}.{body}".encode()
        expected = _b64url(
            hmac.new(secret.encode(), sig_input, hashlib.sha256).digest()
        )
        if not hmac.compare_digest(expected, sig):
            return None
        padded = body + "=" * (4 - len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except (ValueError, KeyError, UnicodeDecodeError):
        return None


def _get_token_from_request() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def token_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token_from_request()
        if not token:
            return (jsonify({"error": "No token provided. Login first."}), 401)
        secret = current_app.config.get("JWT_SECRET_KEY", "default-secret")
        payload = _verify_token(token, secret)
        if not payload:
            return (
                jsonify({"error": "Token is invalid or expired. Please login again."}),
                401,
            )
        return f(payload, *args, **kwargs)

    return decorated


def role_required(required_role):
    """Gate a route behind a role, checked fresh against the database.

    The role stored in the JWT payload reflects whatever the user's role was
    at *login* time. If an admin is later demoted, their existing token would
    otherwise keep saying role="admin" until it expires (up to
    TOKEN_EXPIRY_HOURS later), letting them keep using admin routes, including
    re-promoting themselves. Looking the role up from the database on every
    request closes that gap: a demoted user loses admin access on their very
    next request, regardless of what their token claims.
    """

    def wrapper(f):
        from functools import wraps

        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            db_user = get_user_by_username(current_user.get("username", ""))
            if not db_user:
                return (
                    jsonify({"error": "User no longer exists. Please login again."}),
                    401,
                )
            if db_user["role"] != required_role:
                return (jsonify({"error": "Admin access required."}), 403)
            # Refresh current_user with the live DB values so the view function
            # (and anything it does with current_user) never sees a stale role.
            current_user["role"] = db_user["role"]
            current_user["is_permanent"] = bool(db_user.get("is_permanent", 0))
            return f(current_user, *args, **kwargs)

        return decorated

    return wrapper


@auth_bp.route("/register", methods=["POST"])
def register():
    body = request.get_json(silent=True)
    if not body:
        return (jsonify({"error": "Request body must be JSON."}), 400)
    username = body.get("username", "").strip()
    email = body.get("email", "").strip()
    password = body.get("password", "").strip()
    if not username:
        return (jsonify({"error": "Username is required."}), 400)
    if len(username) < 3:
        return (jsonify({"error": "Username must be at least 3 characters."}), 400)
    if not email or "@" not in email:
        return (jsonify({"error": "Valid email is required."}), 400)
    if not password:
        return (jsonify({"error": "Password is required."}), 400)
    if len(password) < 6:
        return (jsonify({"error": "Password must be at least 6 characters."}), 400)
    result = create_user(username, email, password)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 409)
    return (
        jsonify({"message": "Account created successfully.", "username": username}),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True)
    if not body:
        return (jsonify({"error": "Request body must be JSON."}), 400)
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    if not username or not password:
        return (jsonify({"error": "Username and password are required."}), 400)
    result = authenticate_user(username, password)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 401)
    user = result["user"]
    secret = current_app.config.get("JWT_SECRET_KEY", "default-secret")
    expiry = int(time.time()) + TOKEN_EXPIRY_HOURS * 3600
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "exp": expiry,
    }
    token = _create_token(payload, secret)
    return (
        jsonify(
            {
                "token": token,
                "username": user["username"],
                "expires_in": TOKEN_EXPIRY_HOURS * 3600,
            }
        ),
        200,
    )


@auth_bp.route("/me", methods=["GET"])
@token_required
def me(current_user):
    # Read the role fresh from the database rather than trusting the token
    # payload, so a demoted user immediately sees (and is granted) their
    # correct, current role instead of whatever role they had at login time.
    db_user = get_user_by_username(current_user.get("username", ""))
    if not db_user:
        return (
            jsonify({"error": "User no longer exists. Please login again."}),
            401,
        )
    return (
        jsonify(
            {
                "user_id": db_user["id"],
                "username": db_user["username"],
                "email": db_user["email"],
                "role": db_user["role"],
                "is_permanent_admin": bool(db_user.get("is_permanent", 0)),
            }
        ),
        200,
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    return (jsonify({"message": "Logged out successfully."}), 200)
