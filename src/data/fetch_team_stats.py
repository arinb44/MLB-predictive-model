"""Pulls current-season team hitting and pitching totals from MLB's official
Stats API and joins them with Baseball-Reference team WAR / OPS+
(team_war.csv, from fetch_player_war.py — run that first), for the web UI's
team dot plots (src/api/main.py's /stats/teams).

Informational only — NOT fed into the trained model (season-to-date
snapshots, no point-in-time history; see fetch_statcast_leaderboard.py).

"Offensive rating" in the UI is team OPS+ — the PA-weighted average of the
team's hitters' OPS+, where 100 is league average. The more common wRC+
comes from FanGraphs, which is blocked here (see fetch_player_war.py).
"""
import argparse
import datetime
from pathlib import Path

import pandas as pd
import requests
import yaml

from src.data.teams import MLB_ID_TO_TEAM

TEAM_STATS_URL = "https://statsapi.mlb.com/api/v1/teams/stats"


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_group(season: int, group: str) -> dict[str, dict]:
    params = {"season": season, "group": group, "stats": "season", "sportIds": 1}
    resp = requests.get(TEAM_STATS_URL, params=params, timeout=30)
    resp.raise_for_status()
    splits = resp.json()["stats"][0]["splits"]
    return {MLB_ID_TO_TEAM[s["team"]["id"]]: s["stat"] for s in splits}


def build_team_stats(hitting: dict[str, dict], pitching: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for team, h in hitting.items():
        p = pitching[team]
        games = h["gamesPlayed"]
        pa = h["plateAppearances"]
        rows.append({
            "team": team, "games": games, "wins": p["wins"], "losses": p["losses"],
            "runs": h["runs"], "runs_allowed": p["runs"],
            "runs_per_game": h["runs"] / games, "runs_allowed_per_game": p["runs"] / games,
            "run_diff": h["runs"] - p["runs"],
            "avg": float(h["avg"]), "obp": float(h["obp"]), "slg": float(h["slg"]), "ops": float(h["ops"]),
            "home_runs": h["homeRuns"], "stolen_bases": h["stolenBases"],
            "k_percent": 100 * h["strikeOuts"] / pa, "bb_percent": 100 * h["baseOnBalls"] / pa,
            "era": float(p["era"]), "whip": float(p["whip"]),
            "k_per_9": float(p["strikeoutsPer9Inn"]), "bb_per_9": float(p["walksPer9Inn"]),
            "hr_allowed": p["homeRuns"],
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch current-season team stats for the web UI.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--season", type=int, default=None, help="Defaults to the current year")
    args = parser.parse_args()

    season = args.season or datetime.date.today().year
    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])

    stats = build_team_stats(fetch_group(season, "hitting"), fetch_group(season, "pitching"))
    print(f"fetched team stats for {len(stats)} teams ({season})")

    team_war_path = processed_dir / "team_war.csv"
    if team_war_path.exists():
        stats = stats.merge(pd.read_csv(team_war_path), on="team", how="left")
    else:
        print(f"note: {team_war_path} missing — run fetch_player_war.py first for OPS+/WAR columns")

    out_path = processed_dir / "team_stats.csv"
    stats.round(3).to_csv(out_path, index=False)
    print(f"wrote {out_path}")
