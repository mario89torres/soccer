"""
app.py — Flask server for the Soccer xG/xGA Analyzer
"""

from flask import Flask, render_template, request, jsonify
from scraper import get_team_matches
from predictor import predict_match

app = Flask(__name__)


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

    # Run Poisson + Monte Carlo prediction using the fetched xG averages
    try:
        results["prediction"] = predict_match(results["team1"], results["team2"])
    except Exception as e:
        results["prediction"] = {"error": str(e)}

    return jsonify(results)


if __name__ == "__main__":
    print("Soccer xG Analyzer running at http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
