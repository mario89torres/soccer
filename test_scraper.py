from scraper import get_team_matches
import json

print("Testing Real Madrid...")
data = get_team_matches("Real Madrid", n=5)
print(json.dumps(data, indent=2))
