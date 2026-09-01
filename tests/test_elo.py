"""Proves Elo's pre-game ratings are fixed before that game's own result is
known — the property that makes them usable as a leakage-safe feature.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.elo import compute_elo_ratings  # noqa: E402

CFG = {"elo": {"k_factor": 4, "home_field_advantage": 24, "initial_rating": 1500, "season_regression": 0.25}}


def make_schedule(game0_scores: tuple[int, int]) -> pd.DataFrame:
    """Two games between the same two teams; only game 0's score varies."""
    return pd.DataFrame([
        {
            "game_date": "2023-04-01", "game_number": 1, "season": 2023,
            "home_team": "A", "away_team": "B",
            "home_score": game0_scores[0], "away_score": game0_scores[1],
            "home_win": int(game0_scores[0] > game0_scores[1]),
        },
        {
            "game_date": "2023-04-02", "game_number": 1, "season": 2023,
            "home_team": "B", "away_team": "A",
            "home_score": 3, "away_score": 1,
            "home_win": 1,
        },
    ])


def test_first_game_uses_initial_rating():
    elo_df = compute_elo_ratings(make_schedule((5, 2)), CFG)
    first = elo_df.iloc[0]
    assert first["home_elo_pre"] == 1500
    assert first["away_elo_pre"] == 1500


def test_pregame_rating_unaffected_by_own_game_outcome():
    """Game 0's pre-game ratings must be identical no matter how game 0
    itself turns out — they're computed strictly from ratings entering the
    game, before that game's result is applied.
    """
    blowout = compute_elo_ratings(make_schedule((10, 0)), CFG)
    narrow = compute_elo_ratings(make_schedule((5, 4)), CFG)

    assert blowout.iloc[0]["home_elo_pre"] == narrow.iloc[0]["home_elo_pre"]
    assert blowout.iloc[0]["away_elo_pre"] == narrow.iloc[0]["away_elo_pre"]


def test_next_game_rating_reflects_prior_result():
    """By contrast, game 1's pre-game rating for team A *should* differ
    depending on how game 0 went — that's the update actually taking effect,
    just only after game 0 is over.
    """
    blowout = compute_elo_ratings(make_schedule((10, 0)), CFG)
    loss = compute_elo_ratings(make_schedule((0, 10)), CFG)

    # game 1: home=B, away=A -> compare away_elo_pre (team A's rating)
    assert blowout.iloc[1]["away_elo_pre"] > loss.iloc[1]["away_elo_pre"]


def test_season_regression_moves_ratings_toward_mean():
    """A single 2023 game (so its post-game rating is directly recoverable
    from replaying the update formula), then a 2024 opener whose pre-game
    rating should equal that post-game rating regressed toward the mean.
    """
    from src.models.elo import expected_win_prob, mov_multiplier

    schedule = pd.concat([
        make_schedule((10, 0)).iloc[[0]],
        pd.DataFrame([{
            "game_date": "2024-04-01", "game_number": 1, "season": 2024,
            "home_team": "A", "away_team": "B",
            "home_score": 1, "away_score": 1, "home_win": 0,
        }]),
    ], ignore_index=True)

    elo_df = compute_elo_ratings(schedule, CFG)

    initial = CFG["elo"]["initial_rating"]
    hfa = CFG["elo"]["home_field_advantage"]
    k = CFG["elo"]["k_factor"]
    regression = CFG["elo"]["season_regression"]

    elo_diff = (initial + hfa) - initial
    home_win_prob = expected_win_prob(elo_diff)
    mult = mov_multiplier(elo_diff, run_diff=10)
    shift = k * mult * (1 - home_win_prob)
    end_of_2023_rating = initial + shift  # A's rating after its only 2023 game

    start_of_2024_rating = elo_df.iloc[1]["home_elo_pre"]  # A is home in the 2024 opener
    expected = initial + (1 - regression) * (end_of_2023_rating - initial)

    assert abs(start_of_2024_rating - expected) < 1e-9
    assert start_of_2024_rating != end_of_2023_rating
