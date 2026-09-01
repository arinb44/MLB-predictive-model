"""Raw data pulls via pybaseball. No feature engineering here — just fetch
and reshape into a per-game table. See build_features.py for rolling/
leakage-safe feature computation.
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import pybaseball as pb
import yaml

# pybaseball's disk cache avoids re-hitting Baseball Reference / Savant on reruns.
pb.cache.enable()

TEAMS = [
    "ARI", "ATL", "BAL", "BOS", "CHC", "CHW", "CIN", "CLE", "COL", "DET",
    "HOU", "KCR", "LAA", "LAD", "MIA", "MIL", "MIN", "NYM", "NYY", "OAK",
    "PHI", "PIT", "SDP", "SEA", "SFG", "STL", "TBR", "TEX", "TOR", "WSN",
]


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_team_season(season: int, team: str, retries: int = 3, pause: float = 1.0) -> pd.DataFrame:
    """One team's full-season game log (Baseball Reference schedule/results)."""
    for attempt in range(retries):
        try:
            df = pb.schedule_and_record(season, team)
            df["season"] = season
            return df
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"  retry {team} {season} ({e}); sleeping {pause}s")
            time.sleep(pause)
    raise RuntimeError("unreachable")


def fetch_all_team_seasons(start_season: int, end_season: int, raw_dir: Path,
                            teams: list[str] = TEAMS) -> None:
    """Pull every team's schedule for every season, one CSV per team-season."""
    out_dir = raw_dir / "schedule_and_record"
    out_dir.mkdir(parents=True, exist_ok=True)

    for season in range(start_season, end_season + 1):
        for team in teams:
            dest = out_dir / f"{season}_{team}.csv"
            if dest.exists():
                continue
            print(f"fetching {team} {season}...")
            df = fetch_team_season(season, team)
            df.to_csv(dest, index=False)
            time.sleep(0.5)  # be polite to Baseball Reference


def build_game_log(raw_dir: Path, processed_dir: Path, start_season: int, end_season: int) -> pd.DataFrame:
    """Reshape per-team schedule CSVs into one row per game (home team's row).

    schedule_and_record gives each team's own game log, so every game appears
    twice (once per team). Keeping only the Home_Away == 'Home' rows yields a
    single canonical row per game, with a home-team and opponent perspective.
    """
    sched_dir = raw_dir / "schedule_and_record"
    frames = []
    for season in range(start_season, end_season + 1):
        for path in sorted(sched_dir.glob(f"{season}_*.csv")):
            frames.append(pd.read_csv(path))

    if not frames:
        raise FileNotFoundError(
            f"No schedule files found in {sched_dir} for {start_season}-{end_season}. "
            "Run fetch_all_team_seasons first."
        )

    all_games = pd.concat(frames, ignore_index=True)
    home_games = all_games[all_games["Home_Away"] == "Home"].copy()

    home_games = home_games.rename(columns={
        "Tm": "home_team",
        "Opp": "away_team",
        "R": "home_score",
        "RA": "away_score",
        "W/L": "result",  # from home team's perspective: W/L(-Wo)/L(-Wo) etc.
    })
    home_games["home_win"] = home_games["result"].str.startswith("W").astype(int)
    # Date looks like "Thursday, Jun 8" or "Thursday, Jun 8 (1)"/"(2)" for
    # doubleheaders — strip the weekday prefix and game-number suffix, and
    # keep the suffix separately so doubleheader games remain distinguishable.
    date_str = home_games["Date"].str.replace(r"^\w+, ", "", regex=True)
    home_games["game_number"] = date_str.str.extract(r"\((\d)\)$").fillna(1).astype(int)
    date_str = date_str.str.replace(r"\s*\(\d\)$", "", regex=True)
    home_games["game_date"] = pd.to_datetime(
        date_str + " " + home_games["season"].astype(str),
        format="%b %d %Y",
        errors="coerce",
    )
    home_games = home_games.sort_values(["game_date", "game_number"]).reset_index(drop=True)

    keep_cols = [
        "game_date", "game_number", "season", "home_team", "away_team", "home_score",
        "away_score", "home_win", "D/N", "Attendance", "Streak", "Win", "Loss", "Save", "Inn",
    ]
    game_log = home_games[keep_cols]

    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / "game_log.csv"
    game_log.to_csv(out_path, index=False)
    print(f"wrote {len(game_log)} games to {out_path}")
    return game_log


def fetch_statcast_range(start_dt: str, end_dt: str, raw_dir: Path) -> pd.DataFrame:
    """Pitch-level Statcast data for a date range (used later for matchup/
    pitcher-arsenal features — pulled in chunks since the endpoint is heavy)."""
    out_dir = raw_dir / "statcast"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"statcast_{start_dt}_{end_dt}.csv"
    if dest.exists():
        return pd.read_csv(dest)

    df = pb.statcast(start_dt=start_dt, end_dt=end_dt)
    df.to_csv(dest, index=False)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch raw MLB data via pybaseball.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--start-season", type=int, default=None)
    parser.add_argument("--end-season", type=int, default=None)
    parser.add_argument("--teams", nargs="*", default=None, help="Subset of team codes, e.g. --teams NYY BOS")
    parser.add_argument("--skip-fetch", action="store_true", help="Only rebuild game_log.csv from existing raw files")
    args = parser.parse_args()

    cfg = load_config(args.config)
    start_season = args.start_season or cfg["data"]["start_season"]
    end_season = args.end_season or cfg["data"]["end_season"]
    raw_dir = Path(cfg["data"]["raw_dir"])
    processed_dir = Path(cfg["data"]["processed_dir"])
    teams = args.teams or TEAMS

    if not args.skip_fetch:
        fetch_all_team_seasons(start_season, end_season, raw_dir, teams)

    build_game_log(raw_dir, processed_dir, start_season, end_season)
