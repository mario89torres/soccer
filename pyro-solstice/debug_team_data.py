from understatapi import UnderstatClient

# Test without context manager to avoid the IndexError bug
understat = UnderstatClient()
try:
    teams = understat.league(league="EPL").get_team_data(season="2024")
    print(f"Type of teams: {type(teams)}")
    print(f"Length: {len(teams)}")
    print(f"First item type: {type(teams[0])}")
    print(f"First item: {teams[0]}")
    if isinstance(teams[0], dict):
        print("Keys:", list(teams[0].keys()))
    elif isinstance(teams[0], str):
        print("It's a string key! Iterating as dict items...")
        for k, v in list(teams.items())[:2]:
            print(f"  {k}: {v}")
except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
finally:
    understat.session.close()
