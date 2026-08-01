"""HTTP layer for the Saved Watchlist feature.

All database operations are delegated to watchlist.models. This module only
handles request parsing, input validation, error mapping, and HTTP responses.

token_required (from auth.routes) validates the JWT and passes the decoded
payload dict as the first positional argument to each route function. The
payload contains: user_id, username, email, role, exp.
"""

from __future__ import annotations

import sqlite3

from auth.routes import token_required
from feature_engineering.dataset import get_available_countries
from flask import Blueprint, jsonify, request
from watchlist.models import (
    get_watchlist,
    get_watchlist_count,
    pin_country,
    unpin_country,
)

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/watchlist")

MAX_WATCHLIST_SIZE = 19
MAX_COUNTRY_LEN = 100


@watchlist_bp.route("", methods=["GET"])
@token_required
def get_watchlist_route(current_user):
    """GET /watchlist — return the authenticated user's watchlist."""
    user_id = current_user["user_id"]
    try:
        countries = get_watchlist(user_id)
        return jsonify({"watchlist": countries}), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@watchlist_bp.route("/pin", methods=["POST"])
@token_required
def pin_country_route(current_user):
    """POST /watchlist/pin — add a country to the authenticated user's watchlist."""
    user_id = current_user["user_id"]
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON."}), 400

    country = body.get("country", "")

    # Validate length (empty or > 100 chars)
    if not country or len(country) > MAX_COUNTRY_LEN:
        return (
            jsonify({"error": "Country name must be between 1 and 100 characters."}),
            400,
        )

    # Validate against known countries list
    try:
        available = get_available_countries()
    except Exception:
        available = []
    if country not in available:
        return jsonify({"error": f"Country '{country}' was not recognised."}), 400

    # Enforce size limit before writing
    try:
        count = get_watchlist_count(user_id)
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    if count >= MAX_WATCHLIST_SIZE:
        return (
            jsonify({"error": f"Watchlist limit of {MAX_WATCHLIST_SIZE} reached."}),
            422,
        )

    # Pin the country (INSERT OR IGNORE — duplicate is a silent no-op)
    try:
        pin_country(user_id, country)
        return jsonify({"pinned": country}), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@watchlist_bp.route("/unpin", methods=["DELETE"])
@token_required
def unpin_country_route(current_user):
    """DELETE /watchlist/unpin — remove a country from the authenticated user's watchlist."""
    user_id = current_user["user_id"]
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON."}), 400

    country = body.get("country", "")

    # Validate against known countries list
    try:
        available = get_available_countries()
    except Exception:
        available = []
    if not country or country not in available:
        return jsonify({"error": f"Country '{country}' was not recognised."}), 400

    # Unpin (idempotent — returns 200 even if country was not in watchlist)
    try:
        unpin_country(user_id, country)
        return jsonify({"unpinned": country}), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
