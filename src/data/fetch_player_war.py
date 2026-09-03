"""Pulls current-season player WAR from Baseball-Reference's public daily WAR
files, for the web UI's player dot plots (src/api/main.py's /stats/players).

Informational only — NOT fed into the trained model, for the same reason as
the Statcast leaderboards (see fetch_statcast_leaderboard.py): these files
are full-season-to-date snapshots with no point-in-time history, so there's
no leakage-safe way to use them as training features.

Why Baseball-Reference WAR (bWAR) rather than FanGraphs (fWAR): FanGraphs'
leaderboard API is behind a bot challenge (403) in this environment, same as
pybaseball's FanGraphs scrape. The bref files are plain CSV over HTTP.

The files list one row per player per team stint. This script writes:
- player_war.csv: one row per player per role (hitter / pitcher), stints
  summed, tagged with the player's most recent team. Two-way players (e.g.
  Ohtani) get a row for each role. Pitchers' own plate appearances are
  dropped from the hitter side — that's noise, not a hitting profile.
- team_war.csv: WAR and PA-weighted OPS+ per team, built from the stint rows
  so a traded player's value is credited to the team he produced it for.
"""
import argparse
import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import yaml

from src.data.teams import canonical_team

BAT_URL = "https://www.baseball-reference.com/data/war_daily_bat.txt"
PITCH_URL = "https://www.baseball-reference.com/data/war_daily_pitch.txt"
HEADERS = {"User-Agent": "Mozilla/5.0 (MLB-predictive-model; research use)"}


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_war_file(url: str, season: int) -> pd.DataFrame:
    resp = requests.get(url, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    # The files are UTF-8 but served without a charset, so requests would
    # fall back to ISO-8859-1 and mangle accented names ("HernÃ¡ndez").
    df = pd.read_csv(StringIO(resp.content.decode("utf-8")), low_memory=False)
    df = df[df["year_ID"] == season].copy()
    df["team"] = df["team_ID"].map(canonical_team)
    return df


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.gt(0)
    if not mask.any():
        return float("nan")
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


def build_hitters(bat: pd.DataFrame) -> pd.DataFrame:
    bat = bat[bat["pitcher"] == "N"].sort_values("stint_ID")
    rows = []
    for mlb_id, g in bat.groupby("mlb_ID"):
        rows.append({
            "mlb_id": int(mlb_id), "player_name": g["name_common"].iloc[-1], "role": "hitter",
            "team": g["team"].iloc[-1], "age": g["age"].iloc[-1],
            "war": g["WAR"].sum(), "war_off": g["WAR_off"].sum(), "war_def": g["WAR_def"].sum(),
            "pa": int(g["PA"].sum()), "games": int(g["G"].sum()),
            "ops_plus": _weighted_mean(g["OPS_plus"], g["PA"]),
            "runs_bat": g["runs_bat"].sum(), "runs_field": g["runs_field"].sum(),
        })
    return pd.DataFrame(rows)


def build_pitchers(pitch: pd.DataFrame) -> pd.DataFrame:
    pitch = pitch.sort_values("stint_ID")
    rows = []
    for mlb_id, g in pitch.groupby("mlb_ID"):
        ip_outs = g["IPouts"].sum()
        rows.append({
            "mlb_id": int(mlb_id), "player_name": g["name_common"].iloc[-1], "role": "pitcher",
            "team": g["team"].iloc[-1], "age": g["age"].iloc[-1],
            "war": g["WAR"].sum(), "games": int(g["G"].sum()), "games_started": int(g["GS"].sum()),
            "ip": round(ip_outs / 3, 1),
            "era_plus": _weighted_mean(g["ERA_plus"], g["IPouts"]),
        })
    return pd.DataFrame(rows)


def build_team_war(bat: pd.DataFrame, pitch: pd.DataFrame) -> pd.DataFrame:
    hitters = bat[bat["pitcher"] == "N"]
    hit = hitters.groupby("team").apply(lambda g: pd.Series({
        "hitter_war": g["WAR"].sum(),
        "offense_runs_above_avg": g["runs_above_avg_off"].sum(),
        "ops_plus": _weighted_mean(g["OPS_plus"], g["PA"]),
    }), include_groups=False)
    pit = pitch.groupby("team").agg(pitcher_war=("WAR", "sum"))
    team = hit.join(pit, how="outer")
    team["total_war"] = team["hitter_war"] + team["pitcher_war"]
    return team.reset_index().round(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch current-season Baseball-Reference WAR for the web UI.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--season", type=int, default=None, help="Defaults to the current year")
    args = parser.parse_args()

    season = args.season or datetime.date.today().year
    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])

    bat = fetch_war_file(BAT_URL, season)
    pitch = fetch_war_file(PITCH_URL, season)
    print(f"fetched {len(bat)} batting and {len(pitch)} pitching stint rows for {season}")

    players = pd.concat([build_hitters(bat), build_pitchers(pitch)], ignore_index=True).round(3)
    players.to_csv(processed_dir / "player_war.csv", index=False)
    print(f"wrote {processed_dir / 'player_war.csv'} ({len(players)} rows)")

    team_war = build_team_war(bat, pitch)
    team_war.to_csv(processed_dir / "team_war.csv", index=False)
    print(f"wrote {processed_dir / 'team_war.csv'} ({len(team_war)} teams)")
