from understatapi import UnderstatClient
# Try different league name capitalisations
client = UnderstatClient()
try:
    for league in ["EPL", "La_liga", "La_Liga", "Bundesliga", "Serie_A", "Ligue_1", "RFPL"]:
        try:
            teams = client.league(league=league).get_team_data(season="2024")
            titles = [v.get("title","?") for v in teams.values()][:3]
            print(f"OK  {league}: {titles}")
        except Exception as e:
            print(f"ERR {league}: {e}")
finally:
    client.session.close()
