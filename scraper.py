"""
scraper.py — Soccer xG/xGA data fetcher using understatapi
Retrieves the last N match xG and xGA for a given team name.
"""

import re
from understatapi import UnderstatClient

# Leagues supported by Understat
LEAGUES = ["EPL", "La_Liga", "Bundesliga", "Serie_A", "Ligue_1", "RFPL"]
SEASONS = ["2025", "2024", "2023"]   # current year first


# ─── Fuzzy name matching ───────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", name.lower().strip())


def _match_score(candidate: str, query: str) -> int:
    c, q = _normalize(candidate), _normalize(query)
    c_flat, q_flat = c.replace(" ", ""), q.replace(" ", "")
    if c == q or c_flat == q_flat:
        return 100
    if q in c or c in q or q_flat in c_flat or c_flat in q_flat:
        return 80
    q_words = set(q.split())
    c_words = set(c.split())
    overlap = len(q_words & c_words)
    if overlap:
        return 50 + overlap * 10
    return 0


def _make_client():
    """Create a UnderstatClient without using the context manager (avoids indexerror bug)."""
    return UnderstatClient()


# ─── Team search across all leagues ───────────────────────────────────────────

def find_team(team_name: str) -> tuple:
    """
    Search all leagues/seasons for the best matching team.
    Returns (understat_team_name, display_title, league, season) or raises ValueError.
    """
    best = None
    best_score = 0

    client = _make_client()
    try:
        for season in SEASONS:
            for league in LEAGUES:
                try:
                    # Returns dict keyed by team_id: {id, title, history, ...}
                    teams_dict = client.league(league=league).get_team_data(season=season)
                except Exception:
                    continue

                if not isinstance(teams_dict, dict):
                    continue

                for team_id, team_info in teams_dict.items():
                    if not isinstance(team_info, dict):
                        continue
                    title = team_info.get("title", "")
                    if not title:
                        continue
                    score = _match_score(title, team_name)
                    if score > best_score:
                        best_score = score
                        understat_name = title.replace(" ", "_")
                        best = (understat_name, title, league, season)

                if best_score >= 80:
                    return best
    finally:
        try:
            client.session.close()
        except Exception:
            pass

    if not best or best_score < 40:
        raise ValueError(
            f"Team '{team_name}' not found on Understat. "
            f"Check spelling or try another name. "
            f"Only EPL, La Liga, Bundesliga, Serie A, Ligue 1 and RFPL are supported."
        )
    return best


# ─── Match data fetching ───────────────────────────────────────────────────────

def get_team_matches(team_name: str, n: int = 5) -> dict:
    """
    Return the team's last n completed matches with xG and xGA.

    Returns a dict:
    {
        "team":    "Arsenal",
        "league":  "EPL",
        "season":  "2024",
        "avg_xg":  2.01,
        "avg_xga": 0.89,
        "games": [
            {
                "date":           "2025-01-15",
                "home":           True,
                "opponent":       "Chelsea",
                "goals_scored":   2,
                "goals_conceded": 1,
                "xg":             1.83,
                "xga":            0.74,
                "result":         "W"
            }, ...
        ]
    }
    """
    understat_name, display_title, league, season = find_team(team_name)

    client = _make_client()
    try:
        matches = client.team(team=understat_name).get_match_data(season=season)
    finally:
        try:
            client.session.close()
        except Exception:
            pass

    # Filter to completed matches only
    completed = [m for m in matches if m.get("isResult")]

    if not completed:
        raise RuntimeError(
            f"No completed matches found for '{display_title}' in {season}/{int(season)+1}."
        )

    # Sort descending by datetime, take last n, then reverse for chart order
    completed.sort(key=lambda m: m.get("datetime", ""), reverse=True)
    recent = completed[:n]
    recent.reverse()   # oldest → newest

    games = []
    for m in recent:
        side = m.get("side", "h")          # 'h' or 'a'
        is_home = (side == "h")
        opp_side = "a" if is_home else "h"

        xg_dict    = m.get("xG", {})
        goals_dict = m.get("goals", {})

        xg  = round(float(xg_dict.get(side,     0) or 0), 2)
        xga = round(float(xg_dict.get(opp_side, 0) or 0), 2)
        gs  = int(goals_dict.get(side,     0) or 0)
        gc  = int(goals_dict.get(opp_side, 0) or 0)

        opp_info = m.get(opp_side, {})
        opponent = opp_info.get("title", "Unknown") if isinstance(opp_info, dict) else "Unknown"

        result = "W" if gs > gc else ("D" if gs == gc else "L")

        games.append({
            "date":           m.get("datetime", "")[:10],
            "home":           is_home,
            "opponent":       opponent,
            "goals_scored":   gs,
            "goals_conceded": gc,
            "xg":             xg,
            "xga":            xga,
            "result":         result,
        })

    avg_xg  = round(sum(g["xg"]  for g in games) / len(games), 2) if games else 0
    avg_xga = round(sum(g["xga"] for g in games) / len(games), 2) if games else 0

    # Fetch top players (scorers/assisters)
    top_scorers   = []
    top_assisters = []
    
    client = _make_client()
    try:
        players = client.team(team=understat_name).get_player_data(season=season)
        if players:
            # Sort by goals (desc), then xG (desc)
            scorers = sorted(players, key=lambda x: (int(x.get("goals",0)), float(x.get("xG",0))), reverse=True)
            top_scorers = [{
                "name": p.get("player_name"),
                "goals": int(p.get("goals",0)),
                "xg": round(float(p.get("xG",0)), 2)
            } for p in scorers[:5] if int(p.get("goals",0)) > 0]

            # Sort by assists (desc), then xA (desc)
            assisters = sorted(players, key=lambda x: (int(x.get("assists",0)), float(x.get("xA",0))), reverse=True)
            top_assisters = [{
                "name": p.get("player_name"),
                "assists": int(p.get("assists",0)),
                "xa": round(float(p.get("xA",0)), 2)
            } for p in assisters[:5] if int(p.get("assists",0)) > 0]
    finally:
        try:
            client.session.close()
        except:
            pass

    return {
        "team":         display_title,
        "league":       league,
        "season":       season,
        "avg_xg":       avg_xg,
        "avg_xga":      avg_xga,
        "games":        games,
        "top_scorers":   top_scorers,
        "top_assisters": top_assisters,
    }
