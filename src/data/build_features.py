"""Leakage-safe feature engineering.

Core rule: every feature for game N must be computable using only games
strictly before N. We enforce this mechanically by reshaping to one row per
(team, game), sorting by date, and using `.shift(1)` before any rolling
aggregation — so a team's rolling stats for game N never include game N's
own result. tests/test_features.py checks this holds, rather than just
asserting it here.
"""
import argparse
from pathlib import Path

import pandas as pd
import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def to_team_game_long(game_log: pd.DataFrame) -> pd.DataFrame:
    """Reshape one-row-per-game (home/away columns) into one row per
    (team, game), so trailing form can be computed per team regardless of
    whether that game was home or away.
    """
    common = ["game_date", "game_number", "season", "Inn"]

    home = game_log[common + ["home_team", "away_team", "home_score", "away_score", "home_win"]].copy()
    home = home.rename(columns={
        "home_team": "team", "away_team": "opponent",
        "home_score": "runs_scored", "away_score": "runs_allowed", "home_win": "win",
    })
    home["is_home"] = 1

    away = game_log[common + ["home_team", "away_team", "home_score", "away_score", "home_win"]].copy()
    away = away.rename(columns={
        "away_team": "team", "home_team": "opponent",
        "away_score": "runs_scored", "home_score": "runs_allowed",
    })
    away["win"] = 1 - away["home_win"]
    away = away.drop(columns=["home_win"])
    away["is_home"] = 0

    long_df = pd.concat([home, away], ignore_index=True)
    long_df["run_diff"] = long_df["runs_scored"] - long_df["runs_allowed"]
    return long_df.sort_values(["team", "game_date", "game_number"]).reset_index(drop=True)


def add_rolling_team_form(long_df: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    """Trailing win%/run-diff/runs-scored per team, using only prior games.

    `.shift(1)` moves each team's own-game stats down by one row before the
    rolling window is applied, so the row for game N sees games
    [N-window .. N-1], never N itself.
    """
    long_df = long_df.sort_values(["team", "game_date", "game_number"]).reset_index(drop=True)
    grouped = long_df.groupby("team", group_keys=False)

    for w in windows:
        shifted_win = grouped["win"].shift(1)
        shifted_run_diff = grouped["run_diff"].shift(1)
        shifted_runs_scored = grouped["runs_scored"].shift(1)

        long_df[f"win_pct_last{w}"] = (
            shifted_win.groupby(long_df["team"]).rolling(w, min_periods=1).mean().reset_index(level=0, drop=True)
        )
        long_df[f"run_diff_last{w}"] = (
            shifted_run_diff.groupby(long_df["team"]).rolling(w, min_periods=1).mean().reset_index(level=0, drop=True)
        )
        long_df[f"runs_scored_last{w}"] = (
            shifted_runs_scored.groupby(long_df["team"]).rolling(w, min_periods=1).mean().reset_index(level=0, drop=True)
        )

    # rest days: gap since this team's previous game. Grouped by (team, season)
    # rather than team alone — the raw gap since last season's final game
    # (~180 days) isn't a meaningful "rest" signal and would otherwise show up
    # as a massive outlier on every team's season opener.
    prev_date = long_df.groupby(["team", "season"], group_keys=False)["game_date"].shift(1)
    long_df["rest_days"] = (pd.to_datetime(long_df["game_date"]) - pd.to_datetime(prev_date)).dt.days

    return long_df


def add_bullpen_fatigue(long_df: pd.DataFrame, fatigue_days: int) -> pd.DataFrame:
    """Extra innings a team's bullpen was on the hook for in the trailing
    N calendar days — a proxy for bullpen fatigue without needing pitcher-
    level data. A 9-inning game uses a "normal" amount of bullpen; extra
    innings the day (or two) before genuinely strain relief availability for
    the next game.

    Uses a calendar-day rolling window (not a game-count window like
    win_pct_last{w}) since "fatigue" decays with days off, not with games
    played. `.shift(1)` first, same as everywhere else, so the current
    game's own extra innings never leak into its own fatigue figure.
    """
    long_df = long_df.sort_values(["team", "game_date", "game_number"]).reset_index(drop=True)
    long_df["extra_innings"] = (long_df["Inn"] - 9).clip(lower=0)

    def _trailing_sum(group: pd.DataFrame) -> pd.Series:
        # Keep the group's original (unique, whole-dataframe) row labels on
        # the result rather than the datetime index used for the rolling
        # window. Different teams often share the same set of calendar
        # dates (every team plays most days of the season) — if two groups'
        # returned Series carried identical datetime indices, pandas'
        # groupby.apply concatenation would collapse them into a DataFrame
        # (one column per group) instead of stacking into one flat Series.
        original_index = group.index
        s = group.set_index(pd.to_datetime(group["game_date"]))["extra_innings"]
        result = s.shift(1).rolling(f"{fatigue_days}D").sum()
        result.index = original_index
        return result

    fatigue = long_df.groupby("team", group_keys=False)[["game_date", "extra_innings"]].apply(_trailing_sum)
    long_df[f"bullpen_fatigue_last{fatigue_days}d"] = fatigue
    return long_df


def add_park_factor(game_log: pd.DataFrame, window: int) -> pd.DataFrame:
    """How much a ballpark tends to inflate/deflate scoring (e.g. Coors
    Field), estimated from this dataset itself rather than an external table
    — the trailing average of total runs scored (both teams combined) in a
    team's home games, divided by the league-wide trailing average over the
    same window. >1 means a hitter-friendly park.

    Computed at the game level (grouped by home_team, i.e. by park) rather
    than the team-game long format, since park identity only exists for the
    home side of a game. Same shift-before-rolling discipline as everything
    else in this module.
    """
    game_log = game_log.sort_values(["game_date", "game_number"]).reset_index(drop=True)
    total_runs = game_log["home_score"] + game_log["away_score"]

    # league-wide scoring environment to date, across every game regardless of park
    league_avg = total_runs.shift(1).expanding(min_periods=20).mean()

    # this park's own trailing scoring average
    by_park = game_log.sort_values(["home_team", "game_date", "game_number"])
    park_total_runs = (by_park["home_score"] + by_park["away_score"])
    park_avg = (
        park_total_runs.groupby(by_park["home_team"], group_keys=False).shift(1)
        .groupby(by_park["home_team"]).rolling(window, min_periods=20).mean()
        .reset_index(level=0, drop=True)
    )
    park_avg = park_avg.reindex(game_log.index)  # back to game_log's original (date-sorted) row order

    game_log["park_run_factor"] = park_avg / league_avg
    return game_log


def add_starter_features(
    features: pd.DataFrame, starters_df: pd.DataFrame, trailing_starts: int
) -> pd.DataFrame:
    """Starting-pitcher identity (for the PyTorch embedding model) plus a
    leakage-safe trailing performance proxy usable by every model.

    The proxy is the pitcher's *team's* runs allowed in each of their own
    prior starts, averaged over their trailing `trailing_starts` starts —
    not a true per-pitcher earned-run figure, since Retrosheet's basic game
    log doesn't break runs down by individual pitcher (that needs parsing
    the raw play-by-play event files, out of scope here). It conflates some
    bullpen performance into "starter quality," but it's a real, commonly
    used proxy when full box scores aren't available, and it's still
    computed with the same shift-before-rolling discipline as everything
    else in this module.

    Games with no Retrosheet-sourced starter (2024 as of this build) simply
    get NaN here, handled the same as any other missing rolling feature.
    """
    keys = ["game_date", "game_number", "season", "home_team", "away_team"]
    features = features.merge(starters_df, on=keys, how="left")

    home_starts = features[keys + ["home_pitcher_id", "away_score"]].rename(
        columns={"home_pitcher_id": "pitcher_id", "away_score": "runs_allowed"}
    )
    home_starts["is_home"] = 1
    away_starts = features[keys + ["away_pitcher_id", "home_score"]].rename(
        columns={"away_pitcher_id": "pitcher_id", "home_score": "runs_allowed"}
    )
    away_starts["is_home"] = 0

    starts_long = pd.concat([home_starts, away_starts], ignore_index=True)
    starts_long = starts_long.dropna(subset=["pitcher_id"]).copy()
    starts_long = starts_long.sort_values(["pitcher_id", "game_date", "game_number"]).reset_index(drop=True)

    shifted = starts_long.groupby("pitcher_id", group_keys=False)["runs_allowed"].shift(1)
    proxy_col = f"starter_runs_allowed_last{trailing_starts}"
    starts_long[proxy_col] = (
        shifted.groupby(starts_long["pitcher_id"]).rolling(trailing_starts, min_periods=1).mean()
        .reset_index(level=0, drop=True)
    )

    home_proxy = starts_long[starts_long["is_home"] == 1][keys + [proxy_col]].rename(columns={proxy_col: f"home_{proxy_col}"})
    away_proxy = starts_long[starts_long["is_home"] == 0][keys + [proxy_col]].rename(columns={proxy_col: f"away_{proxy_col}"})

    features = features.merge(home_proxy, on=keys, how="left").merge(away_proxy, on=keys, how="left")
    return features


def build_game_features(
    game_log: pd.DataFrame, windows: list[int], fatigue_days: int = 3, park_window: int = 150
) -> pd.DataFrame:
    long_df = to_team_game_long(game_log)
    long_df = add_rolling_team_form(long_df, windows)
    long_df = add_bullpen_fatigue(long_df, fatigue_days)

    feature_cols = [c for c in long_df.columns if c.startswith(("win_pct_last", "run_diff_last", "runs_scored_last"))]
    feature_cols += ["rest_days", f"bullpen_fatigue_last{fatigue_days}d"]

    key_cols = ["game_date", "game_number", "season", "team"]
    home_feats = long_df[long_df["is_home"] == 1][key_cols + feature_cols].copy()
    home_feats = home_feats.rename(columns={c: f"home_{c}" for c in feature_cols}).rename(columns={"team": "home_team"})

    away_feats = long_df[long_df["is_home"] == 0][key_cols + feature_cols].copy()
    away_feats = away_feats.rename(columns={c: f"away_{c}" for c in feature_cols}).rename(columns={"team": "away_team"})

    features = game_log.merge(
        home_feats, on=["game_date", "game_number", "season", "home_team"], how="left"
    ).merge(
        away_feats, on=["game_date", "game_number", "season", "away_team"], how="left"
    )

    # a few home-minus-away differential features, since relative form matters more than absolute
    for w in windows:
        features[f"win_pct_diff_last{w}"] = features[f"home_win_pct_last{w}"] - features[f"away_win_pct_last{w}"]
        features[f"run_diff_diff_last{w}"] = features[f"home_run_diff_last{w}"] - features[f"away_run_diff_last{w}"]

    features = add_park_factor(features, park_window)

    return features.sort_values(["game_date", "game_number"]).reset_index(drop=True)


def merge_elo_features(features: pd.DataFrame, elo_df: pd.DataFrame) -> pd.DataFrame:
    """Join Elo's pre-game ratings (already leakage-safe by construction —
    see src/models/elo.py) onto the rolling-form feature table."""
    keys = ["game_date", "game_number", "season", "home_team", "away_team"]
    merged = features.merge(
        elo_df[keys + ["home_elo_pre", "away_elo_pre", "elo_home_win_prob"]], on=keys, how="left"
    )
    merged["elo_diff"] = merged["home_elo_pre"] - merged["away_elo_pre"]
    return merged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build leakage-safe rolling features from the game log.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])
    windows = cfg["features"]["rolling_windows"]
    fatigue_days = cfg["features"]["bullpen_fatigue_days"]
    park_window = cfg["features"]["park_factor_window"]

    game_log = pd.read_csv(processed_dir / "game_log.csv")
    features = build_game_features(game_log, windows, fatigue_days=fatigue_days, park_window=park_window)

    elo_path = processed_dir / "elo.csv"
    if elo_path.exists():
        features = merge_elo_features(features, pd.read_csv(elo_path))
    else:
        print(f"note: {elo_path} not found — run src/models/elo.py first to include Elo features")

    starters_path = processed_dir / "starters.csv"
    if starters_path.exists():
        starter_trailing = cfg["features"]["starter_trailing_starts"]
        features = add_starter_features(features, pd.read_csv(starters_path), starter_trailing)
    else:
        print(f"note: {starters_path} not found — run src/data/fetch_pitchers.py first to include starter features")

    out_path = processed_dir / "features.csv"
    features.to_csv(out_path, index=False)
    print(f"wrote {len(features)} rows, {len(features.columns)} columns to {out_path}")
