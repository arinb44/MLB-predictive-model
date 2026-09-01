"""Logistic regression baseline — the floor the GBM and PyTorch models need
to clear. Trained on the leakage-safe features in features.csv.
"""
from pathlib import Path

import pandas as pd
import yaml
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Identifiers and columns that either leak the outcome (scores, result-derived
# columns, or Inn — how many innings *this* game went, unknowable before
# first pitch) or aren't numeric model inputs. Note this list only covers
# raw pass-through columns from game_log.csv; the *rolling*/trailing
# features derived from Inn (bullpen_fatigue_last{w}d) are fine to keep,
# since those are leakage-safe by construction (see build_features.py).
NON_FEATURE_COLS = {
    "game_date", "game_number", "season", "home_team", "away_team",
    "home_score", "away_score", "home_win", "D/N", "Attendance",
    "Streak", "Win", "Loss", "Save", "Inn",
    # pitcher identity is a string ID, not a numeric feature — used directly
    # (as an embedding) only by the PyTorch model, see src/models/nn.py
    "home_pitcher_id", "home_pitcher_name", "away_pitcher_id", "away_pitcher_name",
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_feature_columns(features_df: pd.DataFrame) -> list[str]:
    # win_pct_diff_last{w} / run_diff_diff_last{w} / elo_diff are exact
    # linear combinations of home_*/away_* columns already included (home -
    # away). elo_home_win_prob = sigmoid(elo_diff / 400) is nearly linear
    # over the narrow range Elo ratings occupy in practice, so it's also
    # near-collinear with home_elo_pre/away_elo_pre. A linear model can
    # represent all of this itself via its own coefficients, so keeping the
    # derived columns too makes the design matrix (near-)rank-deficient and
    # destabilizes the L-BFGS solver (overflowing intermediate coefficients
    # before regularization pulls them back). Tree models (GBM) don't have
    # this problem and benefit from the explicit derived columns, so they
    # stay in features.csv — just excluded from the linear baseline's
    # inputs here.
    redundant_cols = {
        c for c in features_df.columns
        if c.startswith("win_pct_diff_last")
        or c.startswith("run_diff_diff_last")
        or c in ("elo_diff", "elo_home_win_prob")
    }
    return [c for c in features_df.columns if c not in NON_FEATURE_COLS and c not in redundant_cols]


def build_pipeline(**logreg_kwargs) -> Pipeline:
    # Early-season rows lack full rolling history (NaN) — impute with the
    # train-fold mean rather than dropping, so we don't lose every team's
    # first few games of every season.
    #
    # solver="liblinear": several remaining features are still correlated
    # even after dropping the exact/near-exact duplicates above (e.g.
    # win_pct_last10 vs. win_pct_last30). lbfgs's line search can overflow
    # on that correlation with modest sample sizes (a walk-forward fold's
    # early seasons); liblinear's coordinate descent doesn't hit this, and
    # it's sklearn's own recommendation for smaller datasets like this one.
    logreg_kwargs.setdefault("solver", "liblinear")
    return Pipeline([
        ("impute", SimpleImputer(strategy="mean")),
        ("scale", StandardScaler()),
        ("logreg", LogisticRegression(max_iter=1000, **logreg_kwargs)),
    ])


def train(train_df: pd.DataFrame, feature_cols: list[str]) -> Pipeline:
    pipeline = build_pipeline()
    pipeline.fit(train_df[feature_cols], train_df["home_win"])
    return pipeline


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fit the logistic regression baseline on all available data (no holdout).")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])
    features_df = pd.read_csv(processed_dir / "features.csv")
    feature_cols = get_feature_columns(features_df)

    model = train(features_df, feature_cols)
    coefs = pd.Series(model.named_steps["logreg"].coef_[0], index=feature_cols).sort_values()
    print("Feature coefficients (standardized):")
    print(coefs.to_string())
