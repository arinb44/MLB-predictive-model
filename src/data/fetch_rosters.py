"""Pulls current active-roster (26-man) player lists per team from MLB's
official Stats API — used only to populate the web UI's pitcher/hitter
dropdowns per team (src/api/main.py's /roster/{team} endpoint). Not part of
the leakage-safe training pipeline.

MLB Stats API player IDs are MLBAM IDs, same scheme as the Statcast
leaderboard (fetch_statcast_leaderboard.py) — both get crosswalked to the
Retrosheet IDs used everywhere else in this project via
pybaseball.chadwick_register().
"""
import argparse
from pathlib import Path

import pandas as pd
import pybaseball as pb
import requests
import yaml

TEAMS_URL = "https://statsapi.mlb.com/api/v1/teams?sportId=1&activeStatus=Y"
ROSTER_URL = "https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active"

# MLB Stats API abbreviations differ from Baseball-Reference's (used
# everywhere else in this project) for a handful of teams.
STATSAPI_TO_BREF = {
    "ATH": "OAK", "ATL": "ATL", "AZ": "ARI", "BAL": "BAL", "BOS": "BOS",
    "CHC": "CHC", "CIN": "CIN", "CLE": "CLE", "COL": "COL", "CWS": "CHW",
    "DET": "DET", "HOU": "HOU", "KC": "KCR", "LAA": "LAA", "LAD": "LAD",
    "MIA": "MIA", "MIL": "MIL", "MIN": "MIN", "NYM": "NYM", "NYY": "NYY",
    "PHI": "PHI", "PIT": "PIT", "SD": "SDP", "SEA": "SEA", "SF": "SFG",
    "STL": "STL", "TB": "TBR", "TEX": "TEX", "TOR": "TOR", "WSH": "WSN",
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_team_ids() -> pd.DataFrame:
    resp = requests.get(TEAMS_URL, timeout=30)
    resp.raise_for_status()
    teams = resp.json()["teams"]
    df = pd.DataFrame([{"team_id": t["id"], "team": STATSAPI_TO_BREF[t["abbreviation"]]} for t in teams])
    return df


def fetch_roster(team_id: int) -> pd.DataFrame:
    resp = requests.get(ROSTER_URL.format(team_id=team_id), timeout=30)
    resp.raise_for_status()
    roster = resp.json()["roster"]
    return pd.DataFrame([{
        "key_mlbam": p["person"]["id"],
        "player_name": p["person"]["fullName"],
        "is_pitcher": p["position"]["abbreviation"] == "P",
    } for p in roster])


def fetch_all_rosters() -> pd.DataFrame:
    team_ids = fetch_team_ids()
    frames = []
    for _, row in team_ids.iterrows():
        roster = fetch_roster(row["team_id"])
        roster["team"] = row["team"]
        frames.append(roster)
    return pd.concat(frames, ignore_index=True)


def add_retro_ids(rosters: pd.DataFrame) -> pd.DataFrame:
    register = pb.chadwick_register()
    crosswalk = register[["key_mlbam", "key_retro"]].dropna(subset=["key_retro"])
    merged = rosters.merge(crosswalk, on="key_mlbam", how="left")
    return merged.dropna(subset=["key_retro"]).rename(columns={"key_retro": "player_id"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch current active rosters for the web UI's team dropdowns.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])

    rosters = fetch_all_rosters()
    print(f"fetched {len(rosters)} active roster spots across {rosters['team'].nunique()} teams")
    rosters = add_retro_ids(rosters)
    print(f"matched {len(rosters)} to Retrosheet IDs")

    out_path = processed_dir / "rosters.csv"
    rosters.to_csv(out_path, index=False)
    print(f"wrote {out_path}")
