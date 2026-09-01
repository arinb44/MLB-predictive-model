"""Runs logistic regression, XGBoost, and the PyTorch entity-embedding model
through the identical walk-forward harness and prints a side-by-side
comparison table — the key artifact for the README's results section.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# import order matters: on macOS, importing xgboost before torch deadlocks
# the process (both bundle their own OpenMP runtime, and xgboost claiming it
# first leaves torch's thread pool unable to initialize). torch must be
# imported first.
from src.models import nn as torch_nn  # noqa: E402
from src.evaluation.backtest import run_walk_forward  # noqa: E402
from src.evaluation.metrics import evaluate_predictions  # noqa: E402
from src.models import baseline, elo, gbm  # noqa: E402


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Side-by-side walk-forward comparison of all models.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--min-train-seasons", type=int, default=3)
    parser.add_argument("--skip-nn", action="store_true", help="Skip the (slower) PyTorch model")
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])
    features_df = pd.read_csv(processed_dir / "features.csv")

    results = {}

    # Elo alone, evaluated on the same games the other models are tested on
    # (elo_home_win_prob is already a leakage-safe pre-game prediction, so no
    # walk-forward fold is needed — it's not "trained" the way the others are).
    elo_probs = features_df["elo_home_win_prob"]
    results["Elo (standalone)"] = evaluate_predictions(features_df["home_win"], elo_probs)

    base_cols = baseline.get_feature_columns(features_df)
    base_preds = run_walk_forward(features_df, base_cols, baseline.train, args.min_train_seasons)
    results["Logistic Regression"] = evaluate_predictions(base_preds["home_win"], base_preds["pred_prob"])
    base_preds.to_csv(processed_dir / "backtest_baseline.csv", index=False)

    gbm_cols = gbm.get_feature_columns(features_df)
    gbm_cfg = cfg["model"]["gbm"]
    gbm_fit = lambda df, cols: gbm.train(  # noqa: E731
        df, cols, n_estimators=gbm_cfg["n_estimators"], max_depth=gbm_cfg["max_depth"], learning_rate=gbm_cfg["learning_rate"]
    )
    gbm_preds = run_walk_forward(features_df, gbm_cols, gbm_fit, args.min_train_seasons)
    results["XGBoost"] = evaluate_predictions(gbm_preds["home_win"], gbm_preds["pred_prob"])
    gbm_preds.to_csv(processed_dir / "backtest_gbm.csv", index=False)

    if not args.skip_nn:
        nn_cols = torch_nn.get_feature_columns(features_df)
        nn_cfg = cfg["model"]["nn"]
        nn_fit = lambda df, cols: torch_nn.train(  # noqa: E731
            df, cols, team_embedding_dim=nn_cfg["team_embedding_dim"], pitcher_embedding_dim=nn_cfg["pitcher_embedding_dim"],
            hidden_dims=tuple(nn_cfg["hidden_dims"]),
            dropout=nn_cfg["dropout"], lr=nn_cfg["lr"], batch_size=nn_cfg["batch_size"], epochs=nn_cfg["epochs"],
        )
        nn_preds = run_walk_forward(features_df, nn_cols, nn_fit, args.min_train_seasons)
        results["PyTorch (entity embeddings)"] = evaluate_predictions(nn_preds["home_win"], nn_preds["pred_prob"])
        nn_preds.to_csv(processed_dir / "backtest_nn.csv", index=False)

    table = pd.DataFrame(results).T[["log_loss", "brier_score", "accuracy", "n"]]
    table = table.round({"log_loss": 4, "brier_score": 4, "accuracy": 4})
    print("\nWalk-forward comparison (all models evaluated on identical test games):\n")
    print(table.to_string())

    out_path = processed_dir / "model_comparison.csv"
    table.to_csv(out_path)
    print(f"\nwrote {out_path}")
