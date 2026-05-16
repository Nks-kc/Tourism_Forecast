import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from auth.models  import init_db
from auth.routes  import auth_bp, token_required
from predict      import predict_all
from config       import API_HOST, API_PORT, SECRET_KEY, JWT_SECRET_KEY, SAVED_MODELS_DIR

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"]     = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

app.register_blueprint(auth_bp)
init_db()

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


@app.route("/", methods=["GET"])
def frontend_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>", methods=["GET"])
def frontend_file(filename):
    if filename in {"index.html", "login.html", "register.html"}:
        return send_from_directory(FRONTEND_DIR, filename)
    return jsonify({"error": "Not found"}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Tourism Forecast API is running"})


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


if __name__ == "__main__":
    print(f"\n  Tourism Forecast API → http://localhost:{API_PORT}\n")
    app.run(host=API_HOST, port=API_PORT, debug=True)
