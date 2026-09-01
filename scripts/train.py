"""Fits the model that gets served (see src/api/main.py) on all available
data — no holdout, since walk-forward evaluation already happened in
scripts/evaluate.py and this is the artifact meant for production use.

Serves logistic regression by default: it's the empirically best model on
this dataset today (see README results), not the doc's original hypothesis
that GBM/PyTorch would win — see the README's Results section for why. Swap
MODEL_TYPE below (and the corresponding branch here) once pitching/park
features close that gap, or to compare a different model in production.
"""
import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import baseline  # noqa: E402

MODEL_TYPE = "logistic_regression"


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fit the production model on all available data.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--out-dir", default="models")
    args = parser.parse_args()

    cfg = load_config(args.config)
    processed_dir = Path(cfg["data"]["processed_dir"])
    features_df = pd.read_csv(processed_dir / "features.csv")

    feature_cols = baseline.get_feature_columns(features_df)
    model = baseline.train(features_df, feature_cols)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model_type": MODEL_TYPE, "pipeline": model, "feature_cols": feature_cols}, out_dir / "production_model.joblib")
    print(f"wrote {out_dir / 'production_model.joblib'} ({MODEL_TYPE}, {len(feature_cols)} features, {len(features_df)} training rows)")
