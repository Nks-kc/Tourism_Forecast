import os
import json
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from auth.models  import init_db
from auth.routes  import auth_bp, token_required
from predict      import predict_all
from config       import API_HOST, API_PORT, SECRET_KEY, JWT_SECRET_KEY, SAVED_MODELS_DIR, PROCESSED_CSV

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"]     = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

app.register_blueprint(auth_bp)
init_db()

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
FRONTEND_DIST_DIR = os.path.join(FRONTEND_DIR, "dist")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Tourism Forecast API is running"})


def season_for_month(month):
    if month in [3, 4, 5]:
        return "spring_trek"
    if month in [6, 7, 8]:
        return "monsoon"
    if month in [9, 10, 11]:
        return "autumn_trek"
    return "shoulder"


@app.route("/history", methods=["GET"])
def history():
    if not os.path.exists(PROCESSED_CSV):
        return jsonify({"error": "Processed tourism data not found."}), 404

    df = pd.read_csv(PROCESSED_CSV, parse_dates=["date"])
    df = df.sort_values("date").copy()
    df["season"] = df["month"].apply(season_for_month)
    df["month_name"] = df["date"].dt.strftime("%b")
    df["date_label"] = df["date"].dt.strftime("%Y-%m")

    try:
        start_year = int(request.args.get("start_year", df["year"].min()))
        end_year = int(request.args.get("end_year", df["year"].max()))
    except ValueError:
        return jsonify({"error": "start_year and end_year must be integers."}), 400

    if start_year > end_year:
        return jsonify({"error": "start_year cannot be greater than end_year."}), 400

    season = request.args.get("season", "all")
    allowed_seasons = {"all", "spring_trek", "monsoon", "autumn_trek", "shoulder"}
    if season not in allowed_seasons:
        return jsonify({"error": f"season must be one of {sorted(allowed_seasons)}."}), 400

    filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()
    if season != "all":
        filtered = filtered[filtered["season"] == season]

    monthly_average = (
        filtered.groupby(["month", "month_name"], as_index=False)["foreign_arrivals"]
        .mean()
        .sort_values("month")
    )
    season_average = (
        df[(df["year"] >= start_year) & (df["year"] <= end_year)]
        .groupby("season", as_index=False)["foreign_arrivals"]
        .mean()
        .sort_values("foreign_arrivals", ascending=False)
    )

    records = [
        {
            "date": row.date_label,
            "year": int(row.year),
            "month": int(row.month),
            "month_name": row.month_name,
            "season": row.season,
            "arrivals": int(row.foreign_arrivals),
        }
        for row in filtered.itertuples(index=False)
    ]

    return jsonify({
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
                "average_arrivals": round(float(row.foreign_arrivals), 2),
            }
            for row in monthly_average.itertuples(index=False)
        ],
        "season_average": [
            {
                "season": row.season,
                "average_arrivals": round(float(row.foreign_arrivals), 2),
            }
            for row in season_average.itertuples(index=False)
        ],
    })


@app.route("/predict", methods=["POST"])
@token_required
def predict(current_user):
    body = request.get_json(silent=True)
    if not body or "horizon" not in body:
        return jsonify({"error": "Body must contain 'horizon'. Example: {\"horizon\": 3}"}), 400
    try:
        horizon = int(body["horizon"])
    except (ValueError, TypeError):
        return jsonify({"error": "'horizon' must be an integer."}), 400
    if horizon not in [1, 3, 6, 12]:
        return jsonify({"error": "'horizon' must be 1, 3, 6, or 12."}), 400
    try:
        predictions = predict_all(horizon)
        return jsonify({"horizon": horizon, "requested_by": current_user["username"], "predictions": predictions})
    except FileNotFoundError as e:
        return jsonify({"error": str(e), "hint": "Run 'python train.py' first."}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/evaluate", methods=["GET"])
@token_required
def evaluate(current_user):
    results_path = os.path.join(SAVED_MODELS_DIR, "results.json")
    if not os.path.exists(results_path):
        return jsonify({"error": "No results found. Run 'python train.py' first."}), 404
    with open(results_path) as f:
        results = json.load(f)
    return jsonify({"metrics": results, "requested_by": current_user["username"]})


@app.route("/", methods=["GET"])
def frontend_index():
    if os.path.exists(os.path.join(FRONTEND_DIST_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    return jsonify({
        "message": "Frontend development app is not built.",
        "hint": "Run 'npm install' and 'npm run dev' inside frontend, or run 'npm run build' to serve it from Flask."
    }), 503


@app.route("/<path:filename>", methods=["GET"])
def frontend_file(filename):
    if os.path.exists(os.path.join(FRONTEND_DIST_DIR, filename)):
        return send_from_directory(FRONTEND_DIST_DIR, filename)
    if os.path.exists(os.path.join(FRONTEND_DIST_DIR, "index.html")) and "." not in filename:
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    print(f"\n  Tourism Forecast API → http://localhost:{API_PORT}\n")
    app.run(host=API_HOST, port=API_PORT, debug=True)
