import os
import json
from functools import lru_cache
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from auth.models import init_db
from auth.routes import auth_bp, token_required
from predict import predict_total, predict_country
from evaluation.comparison import ModelComparison
from feature_engineering.data_loader import load_data
from feature_engineering.dataset import get_available_countries
from feature_engineering.constants import SPRING_MONTHS, AUTUMN_MONTHS, MONSOON_MONTHS
from config import (
    API_HOST,
    API_PORT,
    SECRET_KEY,
    JWT_SECRET_KEY,
    SAVED_MODELS_DIR
)

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.register_blueprint(auth_bp)
init_db()
FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)
FRONTEND_DIST_DIR = os.path.join(FRONTEND_DIR, "dist")
ALLOWED_HORIZONS = [1, 3, 6, 12]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Tourism Forecast API is running"})


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
    raw_df = load_data()
    df = (
        raw_df.groupby("date", as_index=False)
        .agg(arrivals=("arrivals", "sum"))
        .sort_values("date")
    )
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


@app.route("/countries", methods=["GET"])
def countries():
    return jsonify({"countries": get_available_countries()})


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
            predictions = predict_country(country, horizon)
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
    except Exception as e:
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
