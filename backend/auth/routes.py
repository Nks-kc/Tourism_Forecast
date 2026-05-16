"""
auth/routes.py
--------------
Flask Blueprint for authentication endpoints.
Uses JWT tokens stored in the response body (not cookies).
Your frontend stores the token and sends it in the Authorization header.

HOW JWT WORKS (plain English):
  1. User logs in with username + password.
  2. Server verifies credentials, then creates a signed "token" string.
  3. Token contains: user_id, username, expiry time — all encoded + signed.
  4. Frontend stores this token (localStorage or memory).
  5. For every protected API call, frontend sends:
         Authorization: Bearer <token>
  6. Server verifies the signature. If valid, the request is allowed.
  7. Token expires after TOKEN_EXPIRY_HOURS. User must log in again.

ENDPOINTS:
    POST /auth/register   — create new account
    POST /auth/login      — get a JWT token
    GET  /auth/me         — get current user info (requires token)
    POST /auth/logout     — client-side only (just discard the token)
"""

import os
import sys
import json
import hmac
import hashlib
import time
import base64

from flask import Blueprint, request, jsonify, current_app

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.models import create_user, authenticate_user, init_db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

TOKEN_EXPIRY_HOURS = 24


# ── Minimal JWT implementation (no external library needed) ───────────────────

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _create_token(payload: dict, secret: str) -> str:
    """Create a signed JWT token."""
    header  = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body    = _b64url(json.dumps(payload).encode())
    sig_input = f"{header}.{body}".encode()
    sig     = _b64url(hmac.new(secret.encode(), sig_input, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def _verify_token(token: str, secret: str) -> dict | None:
    """
    Verify and decode a JWT token.
    Returns the payload dict if valid and not expired.
    Returns None if invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        sig_input = f"{header}.{body}".encode()
        expected  = _b64url(hmac.new(secret.encode(), sig_input, hashlib.sha256).digest())
        if not hmac.compare_digest(expected, sig):
            return None

        # Decode payload
        padded  = body + "=" * (4 - len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))

        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None


def _get_token_from_request() -> str | None:
    """Extract Bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def token_required(f):
    """
    Decorator for protected routes.
    Usage:
        @auth_bp.route("/protected")
        @token_required
        def protected_route(current_user):
            return jsonify({"user": current_user})
    """
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token_from_request()
        if not token:
            return jsonify({"error": "No token provided. Login first."}), 401

        secret  = current_app.config.get("JWT_SECRET_KEY", "default-secret")
        payload = _verify_token(token, secret)
        if not payload:
            return jsonify({"error": "Token is invalid or expired. Please login again."}), 401

        return f(payload, *args, **kwargs)
    return decorated


# ── Routes ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user account.

    Request body (JSON):
        {
            "username": "john_doe",
            "email":    "john@example.com",
            "password": "mypassword123"
        }

    Response (success):
        { "message": "Account created successfully.", "username": "john_doe" }

    Response (failure):
        { "error": "Username already taken." }
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON."}), 400

    username = body.get("username", "").strip()
    email    = body.get("email",    "").strip()
    password = body.get("password", "").strip()

    # Basic validation
    if not username:
        return jsonify({"error": "Username is required."}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."}), 400
    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required."}), 400
    if not password:
        return jsonify({"error": "Password is required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    result = create_user(username, email, password)
    if not result["ok"]:
        return jsonify({"error": result["error"]}), 409

    return jsonify({
        "message":  "Account created successfully.",
        "username": username,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login and receive a JWT token.

    Request body (JSON):
        { "username": "john_doe", "password": "mypassword123" }

    Response (success):
        {
            "token":    "eyJ...",
            "username": "john_doe",
            "expires_in": 86400
        }

    The frontend should store this token and send it as:
        Authorization: Bearer eyJ...
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON."}), 400

    username = body.get("username", "").strip()
    password = body.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    result = authenticate_user(username, password)
    if not result["ok"]:
        return jsonify({"error": result["error"]}), 401

    user    = result["user"]
    secret  = current_app.config.get("JWT_SECRET_KEY", "default-secret")
    expiry  = int(time.time()) + TOKEN_EXPIRY_HOURS * 3600
    payload = {
        "user_id":  user["id"],
        "username": user["username"],
        "email":    user["email"],
        "exp":      expiry,
    }
    token = _create_token(payload, secret)

    return jsonify({
        "token":      token,
        "username":   user["username"],
        "expires_in": TOKEN_EXPIRY_HOURS * 3600,  # seconds
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def me(current_user):
    """
    Get the currently logged-in user's info.
    Requires: Authorization: Bearer <token>

    Response:
        { "user_id": 1, "username": "john_doe", "email": "john@example.com" }
    """
    return jsonify({
        "user_id":  current_user["user_id"],
        "username": current_user["username"],
        "email":    current_user["email"],
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Logout endpoint.
    JWT is stateless — the server does not store tokens.
    The client simply discards its stored token.
    This endpoint exists so the frontend has a consistent API.

    Response:
        { "message": "Logged out successfully." }
    """
    return jsonify({"message": "Logged out successfully."}), 200
