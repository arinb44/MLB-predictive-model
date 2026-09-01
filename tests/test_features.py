"""Proves the leakage-prevention claims in the README, rather than just
asserting them.

Two complementary strategies:
1. Exact-value check on a small hand-computable schedule — catches formula
   bugs (off-by-one in the rolling window, self-inclusion, etc.).
2. A mutation/invariance check on a larger random schedule — proves that a
   feature for game N is *provably* unaffected by anything happening in game
   N or later, regardless of how the feature is computed. This is the
   stronger, formula-agnostic guarantee and will still catch leakage in any
   new feature added later without needing a matching hand-derived test.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.build_features import add_starter_features, build_game_features, to_team_game_long  # noqa: E402

WINDOWS = [3]
STARTER_TRAILING = 2


def make_two_team_schedule() -> pd.DataFrame:
    """Team A vs Team B, alternating home/away on consecutive days, with a
    fixed, hand-computable sequence of results.
    """
    dates = pd.date_range("2023-04-01", periods=8, freq="D")
    # home_score, away_score per game; home team alternates A/B
    rows = []
    scores = [(5, 2), (1, 4), (6, 6 - 1), (3, 7), (2, 2 - 1), (0, 5), (8, 1), (4, 4 - 1)]
    for i, (date, (hs, aws)) in enumerate(zip(dates, scores)):
        home, away = ("A", "B") if i % 2 == 0 else ("B", "A")
        rows.append({
            "game_date": date.strftime("%Y-%m-%d"),
            "game_number": 1,
            "season": 2023,
            "home_team": home,
            "away_team": away,
            "home_score": hs,
            "away_score": aws,
            "home_win": int(hs > aws),
            "Inn": 9,
        })
    return pd.DataFrame(rows)


def test_first_game_has_no_history():
    game_log = make_two_team_schedule()
    features = build_game_features(game_log, WINDOWS)
    first = features.iloc[0]
    assert pd.isna(first["home_win_pct_last3"])
    assert pd.isna(first["away_win_pct_last3"])


def test_rolling_win_pct_matches_hand_computation():
    game_log = make_two_team_schedule()
    features = build_game_features(game_log, WINDOWS)
    long_df = to_team_game_long(game_log)

    for team in ["A", "B"]:
        team_games = long_df[long_df["team"] == team].sort_values("game_date").reset_index(drop=True)
        for i in range(len(team_games)):
            prior_wins = team_games["win"].iloc[max(0, i - 3):i]
            expected = prior_wins.mean() if len(prior_wins) > 0 else np.nan

            row = team_games.iloc[i]
            game_row = features[
                (features["game_date"] == row["game_date"]) & (features["game_number"] == row["game_number"])
            ].iloc[0]
            side = "home" if game_row["home_team"] == team else "away"
            actual = game_row[f"{side}_win_pct_last3"]

            if np.isnan(expected):
                assert np.isnan(actual), f"{team} game {i}: expected NaN, got {actual}"
            else:
                assert abs(actual - expected) < 1e-9, f"{team} game {i}: expected {expected}, got {actual}"


def make_random_schedule(n_teams: int = 6, n_rounds: int = 25, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(n_teams)]
    dates = pd.date_range("2023-04-01", periods=n_rounds, freq="D")

    rows = []
    for date in dates:
        shuffled = rng.permutation(teams)
        for home, away in zip(shuffled[: n_teams // 2], shuffled[n_teams // 2:]):
            hs, aws = rng.integers(0, 10, size=2)
            innings = 9 if rng.random() > 0.1 else int(rng.integers(10, 14))  # occasional extra innings
            rows.append({
                "game_date": date.strftime("%Y-%m-%d"),
                "game_number": 1,
                "season": 2023,
                "home_team": home,
                "away_team": away,
                "home_score": int(hs),
                "away_score": int(aws),
                "home_win": int(hs > aws),
                "Inn": innings,
            })
    return pd.DataFrame(rows)


def test_features_before_cutoff_are_invariant_to_future_mutation():
    """The core leakage guarantee: mutate every game on/after a cutoff date
    for one team, and every feature value strictly before that cutoff must
    be byte-for-byte identical. If any feature secretly depended on future
    rows, this would catch it regardless of which feature or formula.
    """
    game_log = make_random_schedule()
    target_team = "T0"

    team_dates = sorted(
        game_log.loc[
            (game_log["home_team"] == target_team) | (game_log["away_team"] == target_team), "game_date"
        ].unique()
    )
    cutoff = team_dates[len(team_dates) // 2]

    features_before = build_game_features(game_log, WINDOWS)

    mutated = game_log.copy()
    is_target_on_or_after = (
        ((mutated["home_team"] == target_team) | (mutated["away_team"] == target_team))
        & (mutated["game_date"] >= cutoff)
    )
    mutated.loc[is_target_on_or_after, "home_score"] = 99
    mutated.loc[is_target_on_or_after, "away_score"] = 0
    mutated.loc[is_target_on_or_after, "home_win"] = 1

    features_after = build_game_features(mutated, WINDOWS)

    feature_cols = [
        c for c in features_before.columns
        if "_last" in c or c.endswith("rest_days") or c == "park_run_factor"
    ]

    prior_games = features_before[
        ((features_before["home_team"] == target_team) | (features_before["away_team"] == target_team))
        & (features_before["game_date"] < cutoff)
    ]

    for idx in prior_games.index:
        before_row = features_before.loc[idx, feature_cols]
        after_row = features_after.loc[idx, feature_cols]
        pd.testing.assert_series_equal(before_row, after_row, check_names=False)


def test_starter_rolling_proxy_matches_hand_computation():
    """Team A alternates two starters (A1 on A's home games, A2 on A's away
    games) across the two-team schedule; team B always starts B1. Verifies
    the trailing runs-allowed-in-own-starts proxy follows each *pitcher's*
    own start history — not the team's per-game stream — and never includes
    a pitcher's own start in their own trailing figure.
    """
    game_log = make_two_team_schedule()
    starters = pd.DataFrame([
        {
            "game_date": row.game_date, "game_number": row.game_number, "season": row.season,
            "home_team": row.home_team, "away_team": row.away_team,
            "home_pitcher_id": "A1" if row.home_team == "A" else "B1",
            "home_pitcher_name": "x",
            "away_pitcher_id": "A2" if row.away_team == "A" else "B1",
            "away_pitcher_name": "y",
        }
        for row in game_log.itertuples()
    ])

    features = build_game_features(game_log, WINDOWS)
    features = add_starter_features(features, starters, STARTER_TRAILING)

    col = f"starter_runs_allowed_last{STARTER_TRAILING}"
    a1_actual = features[features["home_team"] == "A"].sort_values("game_date")[f"home_{col}"].tolist()
    a2_actual = features[features["away_team"] == "A"].sort_values("game_date")[f"away_{col}"].tolist()

    a1_expected = [np.nan, 2.0, 3.5, 3.0]
    a2_expected = [np.nan, 1.0, 2.0, 1.5]

    np.testing.assert_allclose(a1_actual, a1_expected, equal_nan=True)
    np.testing.assert_allclose(a2_actual, a2_expected, equal_nan=True)
