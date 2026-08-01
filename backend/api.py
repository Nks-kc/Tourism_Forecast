import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from functools import lru_cache

import pandas as pd
import requests
from auth.models import init_db
from auth.routes import auth_bp, role_required, token_required
from watchlist.models import init_watchlist_table
from watchlist.routes import watchlist_bp
from config import (
    API_HOST,
    API_PORT,
    JWT_SECRET_KEY,
    NOTIFICATION_WEBHOOK_URL,
    SAVED_MODELS_DIR,
    SECRET_KEY,
)
from evaluation.comparison import ModelComparison
from feature_engineering.constants import AUTUMN_MONTHS, MONSOON_MONTHS, SPRING_MONTHS
from feature_engineering.data_ingestion import DataIngestionError, append_monthly_data
from feature_engineering.data_loader import load_data
from feature_engineering.dataset import get_available_countries
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from forecasting.forecast import forecast, get_dataset_last_date
from forecasting.utils import next_month
from predict import predict_country as predict_country_forecast
from predict import predict_total

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.register_blueprint(auth_bp)
app.register_blueprint(watchlist_bp)
init_db()
init_watchlist_table()
FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)
FRONTEND_DIST_DIR = os.path.join(FRONTEND_DIR, "dist")
ALLOWED_HORIZONS = [1, 3, 6, 12]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Tourism Forecast API is running"})


@app.route("/admin/reload", methods=["POST"])
@token_required
@role_required("admin")
def admin_reload(current_user):
    """Clear all in-memory caches so freshly trained models are loaded on next request."""
    from forecasting.forecast import (
        _cached_dataset,
        _cached_holtwinters_model,
        _cached_linear_regression_model,
        _cached_mlp_model,
        _cached_sarima_model,
        _cached_scalers,
        _cached_total_dataset,
        _cached_total_holtwinters_model,
        _cached_total_linear_regression_model,
        _cached_total_mlp_model,
        _cached_total_sarima_model,
        _cached_total_scalers,
    )

    cleared = []
    for fn in [
        _cached_dataset,
        _cached_scalers,
        _cached_mlp_model,
        _cached_linear_regression_model,
        _cached_sarima_model,
        _cached_holtwinters_model,
        _cached_total_dataset,
        _cached_total_scalers,
        _cached_total_mlp_model,
        _cached_total_linear_regression_model,
        _cached_total_sarima_model,
        _cached_total_holtwinters_model,
        _cached_nationwide_history,
        _cached_country_history,
    ]:
        fn.cache_clear()
        cleared.append(fn.__name__)
    return jsonify({"status": "ok", "cleared": cleared})


@app.route("/admin/data", methods=["POST"])
@token_required
@role_required("admin")
def admin_add_data(current_user):
    body = request.get_json(silent=True)
    if not body or "entries" not in body:
        return (jsonify({"error": "Body must contain an 'entries' list."}), 400)

    entries = body["entries"]
    year = body.get("year")
    month = body.get("month")
    overwrite = body.get("overwrite", True)

    try:
        result = append_monthly_data(
            entries, year=year, month=month, overwrite=overwrite
        )
    except DataIngestionError as e:
        return (jsonify({"error": str(e)}), 400)
    except FileNotFoundError as e:
        return (jsonify({"error": str(e)}), 404)

    # New raw rows should show up in history right away
    _cached_nationwide_history.cache_clear()
    _cached_country_history.cache_clear()

    return jsonify(
        {
            "message": "Data ingested successfully.",
            "added": result["added"],
            "updated": result["updated"],
            "total_rows": result["total_rows"],
            "note": "Forecasts still reflect the previous dataset. "
            "Call POST /admin/train to retrain models on the new data.",
            "added_by": current_user["username"],
        }
    )


def _send_notification(payload: dict):
    if not NOTIFICATION_WEBHOOK_URL:
        return
    try:
        requests.post(NOTIFICATION_WEBHOOK_URL, json=payload, timeout=5)
    except requests.RequestException as e:
        app.logger.warning("Notification webhook failed: %s", e)


_training_lock = threading.Lock()
_training_in_progress = False


@app.route("/admin/train", methods=["POST"])
@token_required
@role_required("admin")
def admin_train(current_user):
    if _training_in_progress:
        return (jsonify({"error": "Training already in progress."}), 409)

    triggered_by = current_user["username"]

    def _run_training():
        global _training_in_progress
        with _training_lock:
            _training_in_progress = True
            started_at = datetime.now(tz=timezone.utc)
            try:
                subprocess.run(
                    [sys.executable, "train.py"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    check=True,
                )
                status = "success"
                error = None
            except subprocess.CalledProcessError as e:
                status = "failed"
                error = str(e)
            finally:
                _training_in_progress = False

            finished_at = datetime.now(tz=timezone.utc)
            _send_notification(
                {
                    "event": "training_completed",
                    "status": status,
                    "error": error,
                    "started_by": triggered_by,
                    "started_at": started_at.isoformat(),
                    "finished_at": finished_at.isoformat(),
                    "duration_seconds": (finished_at - started_at).total_seconds(),
                }
            )

    threading.Thread(target=_run_training, daemon=True).start()
    return jsonify(
        {
            "message": "Model retraining started in the background.",
            "started_by": triggered_by,
        }
    ), 202


@app.route("/admin/train/status", methods=["GET"])
@token_required
@role_required("admin")
def admin_train_status(current_user):
    return jsonify({"in_progress": _training_in_progress})


@app.route("/admin/users", methods=["GET"])
@token_required
@role_required("admin")
def admin_list_users(current_user):
    from auth.models import list_users

    return jsonify({"users": list_users()})


@app.route("/admin/users/<username>/role", methods=["PATCH"])
@token_required
@role_required("admin")
def admin_set_user_role(current_user, username):
    from auth.models import get_user_by_username, set_user_role

    body = request.get_json(silent=True)
    if not body or "role" not in body:
        return (jsonify({"error": "Body must contain 'role'."}), 400)
    role = body["role"].strip()
    if role not in ("user", "admin"):
        return (jsonify({"error": "role must be 'user' or 'admin'."}), 400)
    if not get_user_by_username(username):
        return (jsonify({"error": f"User '{username}' not found."}), 404)
    # set_user_role refuses the change and returns ok=False if `username` is
    # the permanent admin and `role` would demote them -- this applies even
    # if current_user (the caller) is that same permanent admin.
    result = set_user_role(username, role)
    if not result["ok"]:
        return (jsonify({"error": result["error"]}), 403)
    return jsonify(
        {
            "message": f"Role of '{username}' set to '{role}'.",
            "updated_by": current_user["username"],
        }
    )


def season_for_month(month):
    if month in SPRING_MONTHS:
        return "spring_trek"
    if month in MONSOON_MONTHS:
        return "monsoon"
    if month in AUTUMN_MONTHS:
        return "autumn_trek"
    return "shoulder"


@lru_cache(maxsize=1)
def _cached_nationwide_history() -> pd.DataFrame:
    from data_store import load_national_arrivals

    df = load_national_arrivals().copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["season"] = df["month"].apply(season_for_month)
    df["month_name"] = df["date"].dt.strftime("%b")
    df["date_label"] = df["date"].dt.strftime("%Y-%m")
    return df


@app.route("/history", methods=["GET"])
def history():
    try:
        df = _cached_nationwide_history()
    except FileNotFoundError as e:
        return (jsonify({"error": str(e)}), 404)
    try:
        start_year = int(request.args.get("start_year", df["year"].min()))
        end_year = int(request.args.get("end_year", df["year"].max()))
    except ValueError:
        return (jsonify({"error": "start_year and end_year must be integers."}), 400)
    if start_year > end_year:
        return (jsonify({"error": "start_year cannot be greater than end_year."}), 400)
    season = request.args.get("season", "all")
    allowed_seasons = {"all", "spring_trek", "monsoon", "autumn_trek", "shoulder"}
    if season not in allowed_seasons:
        return (
            jsonify({"error": f"season must be one of {sorted(allowed_seasons)}."}),
            400,
        )
    filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()
    if season != "all":
        filtered = filtered[filtered["season"] == season]
    monthly_average = (
        filtered.groupby(["month", "month_name"], as_index=False)["arrivals"]
        .mean()
        .sort_values("month")
    )
    season_average = (
        df[(df["year"] >= start_year) & (df["year"] <= end_year)]
        .groupby("season", as_index=False)["arrivals"]
        .mean()
        .sort_values("arrivals", ascending=False)
    )
    records = [
        {
            "date": row.date_label,
            "year": int(row.year),
            "month": int(row.month),
            "month_name": row.month_name,
            "season": row.season,
            "arrivals": int(row.arrivals),
        }
        for row in filtered.itertuples(index=False)
    ]
    return jsonify(
        {
            "meta": {
                "start_year": start_year,
                "end_year": end_year,
                "season": season,
                "records": len(records),
                "min_year": int(df["year"].min()),
                "max_year": int(df["year"].max()),
            },
            "records": records,
            "monthly_average": [
                {
                    "month": int(row.month),
                    "month_name": row.month_name,
                    "average_arrivals": round(float(row.arrivals), 2),
                }
                for row in monthly_average.itertuples(index=False)
            ],
            "season_average": [
                {
                    "season": row.season,
                    "average_arrivals": round(float(row.arrivals), 2),
                }
                for row in season_average.itertuples(index=False)
            ],
        }
    )


@app.route("/predict", methods=["POST"])
@token_required
def predict(current_user):
    body = request.get_json(silent=True)
    if not body or "horizon" not in body:
        return (
            jsonify(
                {"error": "Body must contain 'horizon'. Example: {\"horizon\": 3}"}
            ),
            400,
        )
    try:
        horizon = int(body["horizon"])
    except (ValueError, TypeError):
        return (jsonify({"error": "'horizon' must be an integer."}), 400)
    if horizon not in ALLOWED_HORIZONS:
        return (
            jsonify({"error": f"'horizon' must be one of {ALLOWED_HORIZONS}."}),
            400,
        )
    country = body.get("country") or None
    try:
        if country is not None:
            predictions = predict_country_forecast(country, horizon)
        else:
            predictions = predict_total(horizon)
        return jsonify(
            {
                "horizon": horizon,
                "country": country,
                "requested_by": current_user["username"],
                "predictions": predictions,
            }
        )
    except ValueError as e:
        return (jsonify({"error": str(e)}), 400)
    except FileNotFoundError as e:
        return (jsonify({"error": str(e), "hint": "Run 'python train.py' first."}), 503)
    except (
        EOFError,
        AttributeError,
        ModuleNotFoundError,
        ImportError,
        KeyError,
    ) as e:
        return (jsonify({"error": str(e)}), 500)


@app.route("/evaluate", methods=["GET"])
@token_required
def evaluate(current_user):
    results_path = os.path.join(SAVED_MODELS_DIR, "results.json")
    if not os.path.exists(results_path):
        return (
            jsonify({"error": "No results found. Run 'python train.py' first."}),
            404,
        )
    with open(results_path) as f:
        results = json.load(f)
    return jsonify({"metrics": results, "requested_by": current_user["username"]})


@app.route("/compare", methods=["GET"])
@token_required
def compare(current_user):
    try:
        results = ModelComparison.load_results()
    except FileNotFoundError as e:
        return (jsonify({"error": str(e), "hint": "Run 'python train.py' first."}), 404)
    comparison = ModelComparison.compare(results)
    return jsonify({"comparison": comparison, "requested_by": current_user["username"]})


# ── Country endpoints ────────────────────────────────────────


@app.route("/countries", methods=["GET"])
def countries():
    try:
        country_list = get_available_countries()
        return jsonify({"countries": country_list})
    except (
        FileNotFoundError,
        EOFError,
        AttributeError,
        ModuleNotFoundError,
        ImportError,
        ValueError,
        KeyError,
    ) as e:
        return (jsonify({"error": str(e)}), 500)


@lru_cache(maxsize=64)
def _cached_country_history(country: str) -> pd.DataFrame:
    """Cache per-country history so repeated requests are fast."""
    raw_df = load_data()
    df = raw_df[raw_df["country"] == country].copy()
    if df.empty:
        raise ValueError(f"No data found for country '{country}'.")
    df = df.sort_values("date")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["season"] = df["month"].apply(season_for_month)
    df["month_name"] = df["date"].dt.strftime("%b")
    df["date_label"] = df["date"].dt.strftime("%Y-%m")
    return df


@app.route("/history/country", methods=["GET"])
def history_country():
    country = request.args.get("country", "").strip()
    if not country:
        return (jsonify({"error": "'country' query parameter is required."}), 400)
    try:
        df = _cached_country_history(country)
    except (FileNotFoundError, ValueError) as e:
        return (jsonify({"error": str(e)}), 404)

    try:
        start_year = int(request.args.get("start_year", df["year"].min()))
        end_year = int(request.args.get("end_year", df["year"].max()))
    except ValueError:
        return (jsonify({"error": "start_year and end_year must be integers."}), 400)
    if start_year > end_year:
        return (jsonify({"error": "start_year cannot be greater than end_year."}), 400)

    filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()
    monthly_average = (
        filtered.groupby(["month", "month_name"], as_index=False)["arrivals"]
        .mean()
        .sort_values("month")
    )
    season_average = (
        filtered.groupby("season", as_index=False)["arrivals"]
        .mean()
        .sort_values("arrivals", ascending=False)
    )
    records = [
        {
            "date": row.date_label,
            "year": int(row.year),
            "month": int(row.month),
            "month_name": row.month_name,
            "season": row.season,
            "arrivals": int(row.arrivals),
        }
        for row in filtered.itertuples(index=False)
    ]
    return jsonify(
        {
            "meta": {
                "country": country,
                "start_year": start_year,
                "end_year": end_year,
                "records": len(records),
                "min_year": int(df["year"].min()),
                "max_year": int(df["year"].max()),
            },
            "records": records,
            "monthly_average": [
                {
                    "month": int(row.month),
                    "month_name": row.month_name,
                    "average_arrivals": round(float(row.arrivals), 2),
                }
                for row in monthly_average.itertuples(index=False)
            ],
            "season_average": [
                {
                    "season": row.season,
                    "average_arrivals": round(float(row.arrivals), 2),
                }
                for row in season_average.itertuples(index=False)
            ],
        }
    )


AVAILABLE_MODELS_MAP = {
    "mlp": "MLP",
    "linear_regression": "Linear Regression",
    "sarima": "SARIMA",
    "holtwinters": "Holt-Winters",
}


def _future_month_labels_from(last_date, horizon: int) -> list:
    labels = []
    current_date = last_date
    for _ in range(horizon):
        current_date = next_month(current_date)
        labels.append(current_date.strftime("%Y-%m"))
    return labels


@app.route("/predict/country", methods=["POST"])
@token_required
def predict_country(current_user):
    body = request.get_json(silent=True)
    if not body or "horizon" not in body or "country" not in body:
        return (
            jsonify({"error": "Body must contain 'country' and 'horizon'."}),
            400,
        )
    try:
        horizon = int(body["horizon"])
    except (ValueError, TypeError):
        return (jsonify({"error": "'horizon' must be an integer."}), 400)
    if horizon not in ALLOWED_HORIZONS:
        return (
            jsonify({"error": f"'horizon' must be one of {ALLOWED_HORIZONS}."}),
            400,
        )
    country = str(body["country"]).strip()
    if not country:
        return (jsonify({"error": "'country' must be a non-empty string."}), 400)

    try:
        last_date = get_dataset_last_date()
        months = _future_month_labels_from(last_date, horizon)
        predictions = {}
        import logging as _logging

        _log = _logging.getLogger(__name__)
        for model_key, display_name in AVAILABLE_MODELS_MAP.items():
            try:
                values = forecast(
                    model_name=model_key, country=country, horizon=horizon
                )
                values = [max(0.0, float(v)) for v in values]
                predictions[display_name] = {
                    "months": months,
                    "arrivals": [round(v, 2) for v in values],
                }
            except (
                FileNotFoundError,
                EOFError,
                AttributeError,
                ModuleNotFoundError,
                ImportError,
                ValueError,
                KeyError,
            ) as exc:
                _log.warning(
                    "Skipping model %s for country %s due to error: %s",
                    model_key,
                    country,
                    exc,
                )
        if not predictions:
            return (
                jsonify(
                    {
                        "error": f"No models produced forecasts for '{country}'. This may be a pickle version issue. Run 'python train.py' to retrain.",
                        "hint": "Run 'python train.py' first.",
                    }
                ),
                503,
            )
        return jsonify(
            {
                "country": country,
                "horizon": horizon,
                "requested_by": current_user["username"],
                "predictions": predictions,
            }
        )
    except (ValueError, KeyError) as e:
        return (jsonify({"error": str(e)}), 400)
    except (
        FileNotFoundError,
        EOFError,
        AttributeError,
        ModuleNotFoundError,
        ImportError,
    ) as e:
        return (jsonify({"error": str(e)}), 500)


@app.route("/evaluate/country", methods=["GET"])
@token_required
def evaluate_country(current_user):
    results_path = os.path.join(SAVED_MODELS_DIR, "results_per_country.json")
    if not os.path.exists(results_path):
        return (
            jsonify(
                {"error": "No per-country results found. Run 'python train.py' first."}
            ),
            404,
        )
    with open(results_path) as f:
        results = json.load(f)
    return jsonify({"metrics": results, "requested_by": current_user["username"]})


@app.route("/", methods=["GET"])
def frontend_index():
    if os.path.exists(os.path.join(FRONTEND_DIST_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    return (
        jsonify(
            {
                "message": "Frontend development app is not built.",
                "hint": "Run 'npm install' and 'npm run dev' inside frontend, or run 'npm run build' to serve it from Flask.",
            }
        ),
        503,
    )


@app.route("/<path:filename>", methods=["GET"])
def frontend_file(filename):
    if os.path.exists(os.path.join(FRONTEND_DIST_DIR, filename)):
        return send_from_directory(FRONTEND_DIST_DIR, filename)
    if (
        os.path.exists(os.path.join(FRONTEND_DIST_DIR, "index.html"))
        and "." not in filename
    ):
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    return (jsonify({"error": "Not found"}), 404)


if __name__ == "__main__":
    print(f"\n  Tourism Forecast API -> http://localhost:{API_PORT}\n")
    app.run(host=API_HOST, port=API_PORT, debug=True)
