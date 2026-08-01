from alerts import run_watchlist_alerts
from auth.routes import token_required
from flask import Blueprint, jsonify, request
from notifications import (
    VALID_STATUSES,
    archive_notification,
    delete_notification,
    get_notification_settings,
    list_notifications,
    mark_all_read,
    mark_read,
    update_notification_settings,
)

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("", methods=["GET"])
@token_required
def list_all(current_user):
    status = request.args.get("status")
    if status and status not in VALID_STATUSES:
        return (
            jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}."}),
            400,
        )
    return jsonify(
        {"notifications": list_notifications(current_user["user_id"], status)}
    )


@notifications_bp.route("/<int:notif_id>/read", methods=["POST"])
@token_required
def mark_one_read(current_user, notif_id):
    result = mark_read(current_user["user_id"], notif_id)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 404)
    return jsonify({"message": "Notification marked as read."})


@notifications_bp.route("/read-all", methods=["POST"])
@token_required
def mark_all(current_user):
    result = mark_all_read(current_user["user_id"])
    return jsonify(
        {"message": "All notifications marked as read.", "updated": result["updated"]}
    )


@notifications_bp.route("/<int:notif_id>/archive", methods=["POST"])
@token_required
def archive_one(current_user, notif_id):
    result = archive_notification(current_user["user_id"], notif_id)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 404)
    return jsonify({"message": "Notification archived."})


@notifications_bp.route("/<int:notif_id>", methods=["DELETE"])
@token_required
def delete_one(current_user, notif_id):
    result = delete_notification(current_user["user_id"], notif_id)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 404)
    return jsonify({"message": "Notification deleted."})


@notifications_bp.route("/settings", methods=["GET"])
@token_required
def read_settings(current_user):
    return jsonify({"settings": get_notification_settings(current_user["user_id"])})


@notifications_bp.route("/settings", methods=["PUT", "PATCH"])
@token_required
def write_settings(current_user):
    body = request.get_json(silent=True) or {}
    allowed_keys = {
        "change_threshold_pct",
        "low_arrival_threshold",
        "peak_lookahead_days",
        "email_enabled",
    }
    fields = {k: v for k, v in body.items() if k in allowed_keys}
    if not fields:
        return (
            jsonify(
                {"error": f"Body must contain at least one of {sorted(allowed_keys)}."}
            ),
            400,
        )
    settings = update_notification_settings(current_user["user_id"], **fields)
    return jsonify({"message": "Notification settings updated.", "settings": settings})


@notifications_bp.route("/generate", methods=["POST"])
@token_required
def generate(current_user):
    """Scan the caller's watchlist now and create any alerts that fire.
    Intended to be called on demand or wired up to a scheduler later."""
    created = run_watchlist_alerts(current_user["user_id"])
    return jsonify(
        {
            "message": f"{len(created)} notification(s) generated.",
            "notifications": created,
        }
    )
