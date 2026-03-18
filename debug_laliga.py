from understatapi import UnderstatClient

client = UnderstatClient()
try:
    for season in ["2025", "2024"]:
        for league in ["La_liga"]:
            try:
                teams = client.league(league=league).get_team_data(season=season)
                print(f"{league}/{season}: {len(teams)} teams")
                for k, v in list(teams.items())[:3]:
                    print(f"  {v.get('title', k)}")
                break
            except Exception as e:
                print(f"{league}/{season}: ERROR {e}")
finally:
    client.session.close()
