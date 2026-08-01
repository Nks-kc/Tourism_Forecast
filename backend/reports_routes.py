import os

from auth.routes import token_required
from feature_engineering.dataset import get_available_countries
from flask import Blueprint, jsonify, request, send_file
from report_store import get_report, list_reports, save_report_metadata
from reports import DEFAULT_HORIZON, generate_report
from watchlist import get_watchlist

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("", methods=["GET"])
@token_required
def list_all(current_user):
    return jsonify({"reports": list_reports(current_user["user_id"])})


@reports_bp.route("/generate", methods=["POST"])
@token_required
def generate(current_user):
    body = request.get_json(silent=True) or {}
    report_type = body.get("type", "countries")
    horizon = body.get("horizon", DEFAULT_HORIZON)
    try:
        horizon = int(horizon)
    except (TypeError, ValueError):
        return (jsonify({"error": "'horizon' must be an integer."}), 400)
    if horizon <= 0:
        return (jsonify({"error": "'horizon' must be a positive integer."}), 400)

    if report_type == "watchlist":
        countries = [row["country"] for row in get_watchlist(current_user["user_id"])]
        if not countries:
            return (jsonify({"error": "Your watchlist is empty."}), 400)
    else:
        countries = body.get("countries") or []
        if isinstance(countries, str):
            countries = [countries]
        if not countries:
            return (
                jsonify(
                    {
                        "error": "Body must contain a non-empty 'countries' list, or 'type': 'watchlist'."
                    }
                ),
                400,
            )

    available = set(get_available_countries())
    unknown = [c for c in countries if c not in available]
    if unknown:
        return (
            jsonify(
                {
                    "error": f"Unknown countries: {unknown}. Available: {sorted(available)}"
                }
            ),
            400,
        )

    try:
        path = generate_report(
            current_user["username"], report_type, countries, horizon
        )
    except Exception as e:  # noqa: BLE001 -- surface generation failures as a clean 500
        return (jsonify({"error": f"Report generation failed: {e}"}), 500)

    metadata = save_report_metadata(
        owner_id=current_user["user_id"],
        owner=current_user["username"],
        report_type=report_type,
        countries=countries,
        file_path=str(path),
    )
    return (jsonify({"message": "Report generated.", "report": metadata}), 201)


@reports_bp.route("/<int:report_id>/download", methods=["GET"])
@token_required
def download(current_user, report_id):
    report = get_report(current_user["user_id"], report_id)
    if not report:
        return (jsonify({"error": "Report not found."}), 404)
    if not os.path.exists(report["file_path"]):
        return (jsonify({"error": "Report file is missing on disk."}), 410)
    return send_file(
        report["file_path"],
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"tourism_report_{report_id}.pdf",
    )
