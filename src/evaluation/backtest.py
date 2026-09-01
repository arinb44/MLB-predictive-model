"""Walk-forward (time-aware) evaluation harness. Never trains a model on
data from after the games it's evaluated against — an expanding window that
rolls forward one season at a time. Used identically for every model
(baseline, GBM, PyTorch) so results in the README's comparison table come
from the same evaluation protocol.
"""
from typing import Callable, Iterator

import pandas as pd
import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def walk_forward_seasons(seasons: list[int], min_train_seasons: int) -> Iterator[tuple[list[int], int]]:
    """Expanding-window split: train on every season before test_season,
    then roll forward one season at a time. Requires at least
    `min_train_seasons` prior seasons before the first test season."""
    for i in range(min_train_seasons, len(seasons)):
        yield seasons[:i], seasons[i]


def run_walk_forward(
    features_df: pd.DataFrame,
    feature_cols: list[str],
    fit_fn: Callable[[pd.DataFrame, list[str]], object],
    min_train_seasons: int = 3,
) -> pd.DataFrame:
    """fit_fn(train_df, feature_cols) must return an object exposing
    .predict_proba(X) -> array of shape (n, 2), sklearn-style."""
    seasons = sorted(features_df["season"].unique())
    predictions = []

    for train_seasons, test_season in walk_forward_seasons(seasons, min_train_seasons):
        train_df = features_df[features_df["season"].isin(train_seasons)]
        test_df = features_df[features_df["season"] == test_season]
        if train_df.empty or test_df.empty:
            continue

        model = fit_fn(train_df, feature_cols)
        probs = model.predict_proba(test_df[feature_cols])[:, 1]

        result = test_df[["game_date", "game_number", "season", "home_team", "away_team", "home_win"]].copy()
        result["pred_prob"] = probs
        predictions.append(result)

    if not predictions:
        raise ValueError(
            f"No walk-forward folds produced predictions — need at least "
            f"{min_train_seasons + 1} distinct seasons in features_df (found {len(seasons)})."
        )
    return pd.concat(predictions, ignore_index=True)


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.evaluation.metrics import evaluate_predictions  # noqa: E402
    from src.models.baseline import get_feature_columns, train as train_baseline  # noqa: E402

    parser = argparse.ArgumentParser(description="Walk-forward backtest of the logistic regression baseline.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--min-train-seasons", type=int, default=3)
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])
    features_df = pd.read_csv(processed_dir / "features.csv")
    feature_cols = get_feature_columns(features_df)

    preds = run_walk_forward(features_df, feature_cols, train_baseline, args.min_train_seasons)
    metrics = evaluate_predictions(preds["home_win"], preds["pred_prob"])
    print(f"Walk-forward baseline (logistic regression): {metrics}")

    out_path = processed_dir / "backtest_baseline.csv"
    preds.to_csv(out_path, index=False)
    print(f"wrote {len(preds)} predictions to {out_path}")
