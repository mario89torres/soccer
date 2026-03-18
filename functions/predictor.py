"""
predictor.py — Poisson + Monte Carlo match outcome predictor

Given two teams' avg_xg and avg_xga, estimates:
  - Expected goals each team will score in this match
  - Full scoreline probability matrix (Poisson)
  - Win / Draw / Loss probabilities
  - P(Over 2.5), P(BTTS)
  - Monte Carlo simulation confirming the above
"""

import math
import random


# ── Expected goals model ──────────────────────────────────────────────────────

def expected_goals(team: dict, opponent: dict) -> float:
    """
    Blend the team's attacking average (avg_xg) with what the opponent
    concedes (opponent avg_xga) to get a match-specific goal expectation.
    Simple Dixon-Coles-inspired blending.
    """
    return round((team["avg_xg"] + opponent["avg_xga"]) / 2, 3)


# ── Poisson helpers ───────────────────────────────────────────────────────────

def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) for Poisson(lam)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lam) * lam ** k) / math.factorial(k)


def scoreline_matrix(lam1: float, lam2: float, max_goals: int = 8) -> list[list[float]]:
    """
    matrix[i][j] = P(team1 scores i goals, team2 scores j goals)
    """
    return [
        [poisson_pmf(i, lam1) * poisson_pmf(j, lam2) for j in range(max_goals)]
        for i in range(max_goals)
    ]


def poisson_prediction(team1: dict, team2: dict) -> dict:
    """
    Full Poisson-based prediction.
    Returns probabilities for win/draw/lose and top scorelines.
    """
    lam1 = expected_goals(team1, team2)
    lam2 = expected_goals(team2, team1)

    matrix = scoreline_matrix(lam1, lam2)
    max_g = len(matrix)

    p_team1_win = 0.0
    p_draw      = 0.0
    p_team2_win = 0.0
    p_over_25   = 0.0
    p_btts      = 0.0

    scorelines = []

    for i in range(max_g):
        for j in range(max_g):
            p = matrix[i][j]
            if i > j:
                p_team1_win += p
            elif i == j:
                p_draw      += p
            else:
                p_team2_win += p
            if i + j > 2.5:
                p_over_25 += p
            if i > 0 and j > 0:
                p_btts += p
            scorelines.append((i, j, p))

    # Top 8 most likely scorelines
    scorelines.sort(key=lambda x: x[2], reverse=True)
    top_scorelines = [
        {"score": f"{i}–{j}", "prob": round(p * 100, 1)}
        for i, j, p in scorelines[:8]
    ]

    return {
        "lam1":          lam1,
        "lam2":          lam2,
        "p_team1_win":   round(p_team1_win  * 100, 1),
        "p_draw":        round(p_draw       * 100, 1),
        "p_team2_win":   round(p_team2_win  * 100, 1),
        "p_over_25":     round(p_over_25    * 100, 1),
        "p_btts":        round(p_btts       * 100, 1),
        "top_scorelines": top_scorelines,
    }


# ── Monte Carlo simulation ────────────────────────────────────────────────────

def _poisson_sample(lam: float) -> int:
    """
    Generate a single Poisson-distributed random variate using Knuth's method.
    Efficient enough for small λ (< 30).
    """
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def monte_carlo_simulation(team1: dict, team2: dict, n: int = 100_000) -> dict:
    """
    Simulate n matches via Poisson sampling and return:
    - win/draw/loss counts and probabilities
    - avg goals per sim
    - most frequent scoreline
    """
    lam1 = expected_goals(team1, team2)
    lam2 = expected_goals(team2, team1)

    wins1 = 0
    draws = 0
    wins2 = 0
    total_g1 = 0
    total_g2 = 0
    scoreline_counts: dict[str, int] = {}

    for _ in range(n):
        g1 = _poisson_sample(lam1)
        g2 = _poisson_sample(lam2)
        total_g1 += g1
        total_g2 += g2
        key = f"{g1}–{g2}"
        scoreline_counts[key] = scoreline_counts.get(key, 0) + 1
        if g1 > g2:
            wins1 += 1
        elif g1 == g2:
            draws += 1
        else:
            wins2 += 1

    # Most common scorelines (top 8)
    top = sorted(scoreline_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    return {
        "n_simulations":  n,
        "p_team1_win":    round(wins1 / n * 100, 1),
        "p_draw":         round(draws / n * 100, 1),
        "p_team2_win":    round(wins2 / n * 100, 1),
        "avg_goals_team1": round(total_g1 / n, 2),
        "avg_goals_team2": round(total_g2 / n, 2),
        "top_scorelines": [
            {"score": s, "prob": round(c / n * 100, 1)}
            for s, c in top
        ],
    }


# ── Combined prediction ───────────────────────────────────────────────────────

def predict_match(team1: dict, team2: dict) -> dict:
    """
    Run both Poisson and Monte Carlo predictions and return combined result.
    team1 / team2 must have keys: team, avg_xg, avg_xga
    """
    poisson = poisson_prediction(team1, team2)
    mc      = monte_carlo_simulation(team1, team2, n=100_000)

    # Determine predicted winner by Monte Carlo probability
    if mc["p_team1_win"] > mc["p_team2_win"] and mc["p_team1_win"] > mc["p_draw"]:
        predicted_winner = team1["team"]
        confidence = mc["p_team1_win"]
    elif mc["p_team2_win"] > mc["p_team1_win"] and mc["p_team2_win"] > mc["p_draw"]:
        predicted_winner = team2["team"]
        confidence = mc["p_team2_win"]
    else:
        predicted_winner = "Draw"
        confidence = mc["p_draw"]

    return {
        "team1":             team1["team"],
        "team2":             team2["team"],
        "expected_goals_1":  poisson["lam1"],
        "expected_goals_2":  poisson["lam2"],
        "predicted_winner":  predicted_winner,
        "confidence":        confidence,
        "poisson":           poisson,
        "monte_carlo":       mc,
    }
