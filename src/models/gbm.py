"""Gradient-boosted trees — the primary model, expected to outperform a
plain MLP on this tabular data. Trees handle missing values, non-linear
interactions, and feature collinearity natively, so unlike the linear
baseline this needs no manual feature curation or imputation.

Note for callers that also use src/models/nn.py in the same process (e.g.
scripts/evaluate.py): import torch before xgboost. Both bundle their own
OpenMP runtime, and on macOS, xgboost claiming it first leaves torch's
thread pool unable to initialize — the process hangs with 0% CPU rather than
raising an error.
"""
from pathlib import Path

import pandas as pd
import xgboost as xgb
import yaml

from src.models.baseline import NON_FEATURE_COLS


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_feature_columns(features_df: pd.DataFrame) -> list[str]:
    # Unlike the linear baseline, trees are unaffected by collinear/derived
    # columns (elo_diff, win_pct_diff_last*, etc.) — a split on either side of
    # a redundant column is equivalent, so there's no need to curate them
    # out here. XGBoost also treats NaN (early-season rows without full
    # rolling history yet) as a native missing-value split direction.
    return [c for c in features_df.columns if c not in NON_FEATURE_COLS]


def train(train_df: pd.DataFrame, feature_cols: list[str], **params) -> xgb.XGBClassifier:
    cfg_params = dict(n_estimators=500, max_depth=4, learning_rate=0.03, eval_metric="logloss")
    cfg_params.update(params)
    model = xgb.XGBClassifier(**cfg_params)
    model.fit(train_df[feature_cols], train_df["home_win"])
    return model


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fit the GBM model on all available data (no holdout) and show feature importances.")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])
    features_df = pd.read_csv(processed_dir / "features.csv")
    feature_cols = get_feature_columns(features_df)

    gbm_cfg = cfg["model"]["gbm"]
    model = train(
        features_df, feature_cols,
        n_estimators=gbm_cfg["n_estimators"], max_depth=gbm_cfg["max_depth"], learning_rate=gbm_cfg["learning_rate"],
    )

    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("Feature importances:")
    print(importances.to_string())
