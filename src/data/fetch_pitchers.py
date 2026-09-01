"""Pulls per-game starting-pitcher identity from Retrosheet.

Why not pybaseball's own tools: `team_game_logs(log_type="pitching")` raises
RuntimeError upstream (site structure changed), and deriving starters from a
full Statcast pull would mean pulling pitch-level data for 10 seasons x 30
teams — a multi-hour fetch just to answer "who started."

Why not pybaseball.retrosheet.season_game_logs() directly: it's also
broken. It validates the season file exists via `Github(GH_TOKEN)` with an
empty token, which newer PyGithub versions reject outright
(`AssertionError: assert len(token) > 0`) before ever reaching the actual
data pull. Separately, the retrosheet repo has since moved game logs from
`gamelog/GL{season}.TXT` to `seasons/{season}/GL{season}.TXT`, so even a
successful validation call would point at a stale path. This module
bypasses the validation and fetches directly — the actual pull is a public,
unauthenticated file on raw.githubusercontent.com.

Coverage: 2015-2023. Retrosheet's 2024 season directory exists but has no
GL2024.TXT yet (only the schedule) as of this build — 2024 games simply get
no pitcher data, which the rest of the pipeline already treats as a normal
missing-value case (unknown-pitcher embedding bucket, NaN in rolling stats).
"""
import argparse
from io import StringIO
from pathlib import Path

import pandas as pd
import pybaseball.retrosheet as rs
import yaml

GAMELOG_URL = "https://raw.githubusercontent.com/chadwickbureau/retrosheet/master/seasons/{season}/GL{season}.TXT"

# Retrosheet team codes differ from Baseball-Reference's (used everywhere
# else in this project) for teams whose Retrosheet code doesn't match their
# common abbreviation.
RETROSHEET_TO_BREF = {
    "ANA": "LAA", "ARI": "ARI", "ATL": "ATL", "BAL": "BAL", "BOS": "BOS",
    "CHA": "CHW", "CHN": "CHC", "CIN": "CIN", "CLE": "CLE", "COL": "COL",
    "DET": "DET", "HOU": "HOU", "KCA": "KCR", "LAN": "LAD", "MIA": "MIA",
    "MIL": "MIL", "MIN": "MIN", "NYA": "NYY", "NYN": "NYM", "OAK": "OAK",
    "PHI": "PHI", "PIT": "PIT", "SDN": "SDP", "SEA": "SEA", "SFN": "SFG",
    "SLN": "STL", "TBA": "TBR", "TEX": "TEX", "TOR": "TOR", "WAS": "WSN",
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_season_game_log(season: int) -> pd.DataFrame:
    text = rs.get_text_file(GAMELOG_URL.format(season=season))
    if text.strip().startswith("404"):
        raise FileNotFoundError(f"No Retrosheet game log published yet for {season}")
    data = pd.read_csv(StringIO(text), header=None, sep=",", quotechar='"')
    data.columns = rs.gamelog_columns
    return data


def extract_starters(game_log: pd.DataFrame, season: int) -> pd.DataFrame:
    df = game_log[[
        "date", "game_num", "visiting_team", "home_team",
        "visiting_starting_pitcher_id", "visiting_starting_pitcher_name",
        "home_starting_pitcher_id", "home_starting_pitcher_name",
    ]].copy()

    df["game_date"] = pd.to_datetime(df["date"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
    df["game_number"] = df["game_num"].replace(0, 1)  # Retrosheet: 0 = single game; ours: 1-indexed always
    df["season"] = season
    df["home_team"] = df["home_team"].map(RETROSHEET_TO_BREF)
    df["away_team"] = df["visiting_team"].map(RETROSHEET_TO_BREF)

    df = df.rename(columns={
        "home_starting_pitcher_id": "home_pitcher_id",
        "home_starting_pitcher_name": "home_pitcher_name",
        "visiting_starting_pitcher_id": "away_pitcher_id",
        "visiting_starting_pitcher_name": "away_pitcher_name",
    })
    return df[[
        "game_date", "game_number", "season", "home_team", "away_team",
        "home_pitcher_id", "home_pitcher_name", "away_pitcher_id", "away_pitcher_name",
    ]]


def fetch_all_seasons(start_season: int, end_season: int, raw_dir: Path) -> pd.DataFrame:
    out_dir = raw_dir / "retrosheet"
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for season in range(start_season, end_season + 1):
        dest = out_dir / f"starters_{season}.csv"
        if not dest.exists():
            try:
                print(f"fetching Retrosheet game log {season}...")
                game_log = fetch_season_game_log(season)
            except FileNotFoundError as e:
                print(f"  skipping {season}: {e}")
                continue
            starters = extract_starters(game_log, season)
            starters.to_csv(dest, index=False)
        frames.append(pd.read_csv(dest))

    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch starting-pitcher identity per game via Retrosheet.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    raw_dir = Path(cfg["data"]["raw_dir"])
    processed_dir = Path(cfg["data"]["processed_dir"])

    starters = fetch_all_seasons(cfg["data"]["start_season"], cfg["data"]["end_season"], raw_dir)

    out_path = processed_dir / "starters.csv"
    starters.to_csv(out_path, index=False)
    print(f"wrote {len(starters)} rows ({starters['season'].min()}-{starters['season'].max()}) to {out_path}")
