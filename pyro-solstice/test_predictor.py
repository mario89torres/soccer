from predictor import predict_match
import json

team1 = {"team": "Arsenal",     "avg_xg": 1.89, "avg_xga": 0.80}
team2 = {"team": "Real Madrid", "avg_xg": 1.89, "avg_xga": 1.35}

result = predict_match(team1, team2)
print(json.dumps(result, indent=2))
