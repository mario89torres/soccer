# functions/main.py
from firebase_functions import https_fn
from firebase_admin import initialize_app
from flask import Flask, render_template, request, jsonify
import sys
import os

# Ensure the local directory is in path for imports
sys.path.append(os.path.dirname(__file__))

from scraper import get_team_matches
from predictor import predict_match

initialize_app()

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    team1_name = (data.get("team1") or "").strip()
    team2_name = (data.get("team2") or "").strip()

    if not team1_name or not team2_name:
        return jsonify({"error": "Both team names are required."}), 400

    results = {}
    errors  = []

    for key, name in [("team1", team1_name), ("team2", team2_name)]:
        try:
            results[key] = get_team_matches(name, n=5)
        except ValueError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Error fetching data for '{name}': {e}")

    if errors:
        return jsonify({"error": " | ".join(errors)}), 404

    try:
        results["prediction"] = predict_match(results["team1"], results["team2"])
    except Exception as e:
        results["prediction"] = {"error": str(e)}

    return jsonify(results)

@https_fn.on_request()
def pyro_solstice_xg(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
