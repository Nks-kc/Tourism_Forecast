from auth.routes import token_required
from flask import Blueprint, jsonify, request
from preferences import get_preferences, reset_preferences, update_preferences

preferences_bp = Blueprint("preferences", __name__, url_prefix="/preferences")


@preferences_bp.route("", methods=["GET"])
@token_required
def read_preferences(current_user):
    return jsonify({"preferences": get_preferences(current_user["user_id"])})


@preferences_bp.route("", methods=["PUT", "PATCH"])
@token_required
def write_preferences(current_user):
    body = request.get_json(silent=True)
    if not body:
        return (jsonify({"error": "Request body must be JSON."}), 400)
    allowed_keys = {"default_horizon", "preferred_countries", "theme", "chart_filters"}
    fields = {k: v for k, v in body.items() if k in allowed_keys}
    if not fields:
        return (
            jsonify(
                {"error": f"Body must contain at least one of {sorted(allowed_keys)}."}
            ),
            400,
        )
    result = update_preferences(current_user["user_id"], **fields)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 400)
    return jsonify(
        {"message": "Preferences updated.", "preferences": result["preferences"]}
    )


@preferences_bp.route("/reset", methods=["POST"])
@token_required
def reset(current_user):
    result = reset_preferences(current_user["user_id"])
    return jsonify(
        {
            "message": "Preferences reset to defaults.",
            "preferences": result["preferences"],
        }
    )
