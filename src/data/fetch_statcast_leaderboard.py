"""Pulls current-season Statcast pitcher and batter quality metrics from
Baseball Savant's custom-leaderboard CSV export, for display alongside the
API's predictions.

Informational only — NOT fed into the trained model. Two reasons:
1. There's no leakage-safe historical, point-in-time version of this data
   to train on: this endpoint only returns full-season-to-date cumulative
   stats (confirmed by testing several date-filter parameter conventions —
   start_date/end_date, startDate/endDate, game_date_gt/game_date_lt — all
   silently ignored), so there's no way to reconstruct "what this player's
   Statcast profile looked like as of some past game" for 2015-2023.
2. For pitchers specifically, substituting it into the model's existing
   `starter_runs_allowed_last{w}` feature would be a different, riskier
   move: that feature was fit on team *total* runs allowed (earned +
   unearned, includes bullpen) per start; ERA is earned-only, per-9-innings,
   season-cumulative. Feeding a differently-distributed value into a slot
   the model calibrated on the old signal could quietly hurt predictions in
   a way that's hard to detect without the historical data in point 1 to
   validate against. Batters were never a model input at all (no batter
   data anywhere in training), so there's no substitution risk there — it's
   purely additive display context.

Unlike pybaseball's FanGraphs scrape (blocked, 403 in this environment),
this Baseball Savant endpoint is directly and freely fetchable with a plain
HTTP GET, confirmed for both the current season and past seasons, and for
both player types.

Player IDs here are MLBAM IDs; the rest of this project uses Retrosheet IDs
(see fetch_pitchers.py) for pitcher identity, so this module also builds the
crosswalk via pybaseball.chadwick_register().
"""
import argparse
import datetime
from io import StringIO
from pathlib import Path

import pandas as pd
import pybaseball as pb
import requests
import yaml

LEADERBOARD_URL = "https://baseballsavant.mlb.com/leaderboard/custom"
PITCHER_COLUMNS = [
    "p_era", "p_earned_run", "p_out", "p_win", "p_loss", "woba", "xwoba",
    "k_percent", "bb_percent", "whiff_percent", "hard_hit_percent", "barrel_batted_rate",
]
BATTER_COLUMNS = [
    "batting_avg", "slg_percent", "on_base_percent", "b_rbi", "r_run",
    "woba", "xwoba", "k_percent", "bb_percent", "hard_hit_percent", "barrel_batted_rate",
]


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_leaderboard(season: int, player_type: str, columns: list[str]) -> pd.DataFrame:
    params = {
        "year": season, "type": player_type, "filter": "", "min": "1",
        "selections": ",".join(columns),
        "chart": "false", "x": "xwoba", "y": "xwoba", "r": "no", "chartType": "beeswarm", "csv": "true",
    }
    resp = requests.get(LEADERBOARD_URL, params=params, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    return df.rename(columns={"player_id": "key_mlbam"})


def build_retro_lookup(leaderboard: pd.DataFrame, register: pd.DataFrame, id_col: str) -> pd.DataFrame:
    crosswalk = register[["key_mlbam", "key_retro"]].dropna(subset=["key_retro"])
    merged = leaderboard.merge(crosswalk, on="key_mlbam", how="left")
    return merged.dropna(subset=["key_retro"]).rename(columns={"key_retro": id_col})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch current-season Statcast leaderboards for the live API.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--season", type=int, default=None, help="Defaults to the current year")
    args = parser.parse_args()

    season = args.season or datetime.date.today().year

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])
    register = pb.chadwick_register()

    pitchers = fetch_leaderboard(season, "pitcher", PITCHER_COLUMNS)
    print(f"fetched {len(pitchers)} pitchers for {season}")
    pitcher_lookup = build_retro_lookup(pitchers, register, id_col="pitcher_id")
    print(f"matched {len(pitcher_lookup)} to Retrosheet IDs")
    pitcher_lookup.to_csv(processed_dir / "statcast_leaderboard.csv", index=False)
    print(f"wrote {processed_dir / 'statcast_leaderboard.csv'}")

    batters = fetch_leaderboard(season, "batter", BATTER_COLUMNS)
    print(f"fetched {len(batters)} batters for {season}")
    batter_lookup = build_retro_lookup(batters, register, id_col="player_id")
    print(f"matched {len(batter_lookup)} to Retrosheet IDs")
    batter_lookup.to_csv(processed_dir / "statcast_batters.csv", index=False)
    print(f"wrote {processed_dir / 'statcast_batters.csv'}")
