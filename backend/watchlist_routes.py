from auth.routes import token_required
from flask import Blueprint, jsonify, request
from watchlist import add_country, get_watchlist, remove_country, reorder_watchlist

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/watchlist")


@watchlist_bp.route("", methods=["GET"])
@token_required
def list_watchlist(current_user):
    return jsonify({"watchlist": get_watchlist(current_user["user_id"])})


@watchlist_bp.route("", methods=["POST"])
@token_required
def add_to_watchlist(current_user):
    body = request.get_json(silent=True)
    if not body or "country" not in body:
        return (jsonify({"error": "Body must contain 'country'."}), 400)
    result = add_country(current_user["user_id"], str(body["country"]))
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 409)
    return (
        jsonify(
            {
                "message": "Country added to watchlist.",
                "watchlist": get_watchlist(current_user["user_id"]),
            }
        ),
        201,
    )


@watchlist_bp.route("/<country>", methods=["DELETE"])
@token_required
def remove_from_watchlist(current_user, country):
    result = remove_country(current_user["user_id"], country)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 404)
    return jsonify(
        {
            "message": "Country removed from watchlist.",
            "watchlist": get_watchlist(current_user["user_id"]),
        }
    )


@watchlist_bp.route("/reorder", methods=["PUT"])
@token_required
def reorder(current_user):
    body = request.get_json(silent=True)
    if not body or "countries" not in body or not isinstance(body["countries"], list):
        return (jsonify({"error": "Body must contain a 'countries' list."}), 400)
    result = reorder_watchlist(current_user["user_id"], body["countries"])
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 400)
    return jsonify(
        {
            "message": "Watchlist reordered.",
            "watchlist": get_watchlist(current_user["user_id"]),
        }
    )
