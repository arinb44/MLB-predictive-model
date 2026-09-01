"""Elo rating system for MLB teams, implemented from scratch — the same core
technique FiveThirtyEight used publicly for MLB: logistic win expectation,
home-field advantage, a margin-of-victory multiplier from run differential,
and between-season regression toward the mean.

Used two ways: (1) standalone baseline — its implied win probability alone
is a real, if crude, model; (2) as leakage-safe input features (home_elo_pre,
away_elo_pre) for the GBM/PyTorch models, since we record ratings *before*
each game's result is applied.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def expected_win_prob(rating_diff: float) -> float:
    """Standard logistic Elo expectation. rating_diff = team_a - team_b,
    already including any home-field adjustment."""
    return 1.0 / (1.0 + 10 ** (-rating_diff / 400))


def mov_multiplier(elo_diff: float, run_diff: int) -> float:
    """FiveThirtyEight's margin-of-victory multiplier: bigger blowouts move
    ratings more, but the effect is dampened when the team favored by Elo
    wins big, since that outcome was already expected and less informative.
    """
    return np.log(abs(run_diff) + 1) * (2.2 / (abs(elo_diff) * 0.001 + 2.2))


def compute_elo_ratings(game_log: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Chronologically replay every game, tracking each team's Elo rating.

    For each game we record the *pre-game* ratings — what would have been
    knowable before first pitch — before applying that game's update. This
    is what makes Elo usable as a leakage-safe feature: home_elo_pre/
    away_elo_pre for game N are fixed before game N's own result is known.
    """
    elo_cfg = cfg["elo"]
    k = elo_cfg["k_factor"]
    hfa = elo_cfg["home_field_advantage"]
    initial = elo_cfg["initial_rating"]
    regression = elo_cfg["season_regression"]

    game_log = game_log.sort_values(["season", "game_date", "game_number"]).reset_index(drop=True)

    ratings: dict[str, float] = {}
    current_season = None
    rows = []

    for _, game in game_log.iterrows():
        season = game["season"]
        if current_season is not None and season != current_season:
            ratings = {team: initial + (1 - regression) * (r - initial) for team, r in ratings.items()}
        current_season = season

        home, away = game["home_team"], game["away_team"]
        home_elo = ratings.get(home, initial)
        away_elo = ratings.get(away, initial)

        elo_diff = (home_elo + hfa) - away_elo
        home_win_prob = expected_win_prob(elo_diff)

        rows.append({
            "game_date": game["game_date"],
            "game_number": game["game_number"],
            "season": season,
            "home_team": home,
            "away_team": away,
            "home_elo_pre": home_elo,
            "away_elo_pre": away_elo,
            "elo_home_win_prob": home_win_prob,
        })

        # A game with no result yet (e.g. a not-yet-played game appended by
        # the API to get its pre-game ratings) contributes its pre-game
        # snapshot above but can't update anything — there's no outcome to
        # learn from.
        if pd.isna(game["home_win"]):
            continue

        run_diff = game["home_score"] - game["away_score"]
        home_win = int(game["home_win"])
        mult = mov_multiplier(elo_diff, run_diff)
        shift = k * mult * (home_win - home_win_prob)

        ratings[home] = home_elo + shift
        ratings[away] = away_elo - shift

    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute Elo ratings from the game log.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])

    game_log = pd.read_csv(processed_dir / "game_log.csv")
    elo_df = compute_elo_ratings(game_log, cfg)

    out_path = processed_dir / "elo.csv"
    elo_df.to_csv(out_path, index=False)
    print(f"wrote {len(elo_df)} rows to {out_path}")

    from sklearn.metrics import brier_score_loss, log_loss

    merged = game_log.merge(
        elo_df[["game_date", "game_number", "season", "home_team", "away_team", "elo_home_win_prob"]],
        on=["game_date", "game_number", "season", "home_team", "away_team"],
    )
    ll = log_loss(merged["home_win"], merged["elo_home_win_prob"])
    brier = brier_score_loss(merged["home_win"], merged["elo_home_win_prob"])
    acc = ((merged["elo_home_win_prob"] > 0.5).astype(int) == merged["home_win"]).mean()
    print(f"Elo-only baseline: log-loss={ll:.4f}, brier={brier:.4f}, accuracy={acc:.4f}")
