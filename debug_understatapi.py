from understatapi import UnderstatClient

with UnderstatClient() as understat:
    data = understat.team(team="Manchester_City").get_match_data(season="2024")
    print(f"Got {len(data)} matches")
    if data:
        print("First match keys:", list(data[0].keys()))
        print("First match:", data[0])
        print()
        print("Last 5 matches:")
        for m in data[-5:]:
            print(f"  {m.get('datetime','?')[:10]} vs {m.get('a_team','?') if m.get('side')=='h' else m.get('h_team','?')} | xG={m.get('xG','?')} xGA={m.get('xGA','?')} side={m.get('side','?')}")
