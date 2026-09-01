"""SHAP feature-importance artifacts for the GBM and logistic regression
models — answers "what is the model actually using," which log-loss/
accuracy alone don't. A portfolio/explainability artifact, not a new
production input: nothing here feeds back into training or serving.

GBM uses shap.TreeExplainer (exact, fast, native to boosted trees).
Logistic regression uses shap.LinearExplainer on the fitted coefficients in
the *transformed* (imputed + scaled) feature space — exact and fast for a
linear model, unlike a generic Kernel/PermutationExplainer, which would be
slow and only approximate here for no benefit (the model already IS linear
in that space, so there's a closed-form answer).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models import baseline, gbm  # noqa: E402


def explain_gbm(features_df: pd.DataFrame, out_dir: Path) -> pd.Series:
    feature_cols = gbm.get_feature_columns(features_df)
    model = gbm.train(features_df, feature_cols)
    X = features_df[feature_cols]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X)

    plt.figure()
    shap.summary_plot(shap_values, X, show=False, plot_size=(9, 6))
    plt.tight_layout()
    plt.savefig(out_dir / "shap_gbm_summary.png", dpi=150)
    plt.close()

    importance = pd.Series(np.abs(shap_values.values).mean(axis=0), index=feature_cols)
    return importance.sort_values(ascending=False)


def explain_baseline(features_df: pd.DataFrame, out_dir: Path) -> pd.Series:
    feature_cols = baseline.get_feature_columns(features_df)
    model = baseline.train(features_df, feature_cols)

    # model[:-1] is the impute+scale sub-pipeline; transform without the
    # final logreg step to get the exact space the coefficients operate in.
    X_transformed = model[:-1].transform(features_df[feature_cols])
    X_transformed = pd.DataFrame(X_transformed, columns=feature_cols)
    logreg = model.named_steps["logreg"]

    explainer = shap.LinearExplainer(logreg, X_transformed)
    shap_values = explainer(X_transformed)

    plt.figure()
    shap.summary_plot(shap_values, X_transformed, show=False, plot_size=(9, 6))
    plt.tight_layout()
    plt.savefig(out_dir / "shap_baseline_summary.png", dpi=150)
    plt.close()

    importance = pd.Series(np.abs(shap_values.values).mean(axis=0), index=feature_cols)
    return importance.sort_values(ascending=False)


if __name__ == "__main__":
    import argparse

    import yaml

    parser = argparse.ArgumentParser(description="Generate SHAP feature-importance artifacts for GBM and logistic regression.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--out-dir", default="reports")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    processed_dir = Path(cfg["data"]["processed_dir"])
    features_df = pd.read_csv(processed_dir / "features.csv")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True)

    gbm_importance = explain_gbm(features_df, out_dir)
    gbm_importance.to_csv(out_dir / "shap_gbm_importance.csv", header=["mean_abs_shap"])
    print("GBM top features (mean |SHAP|):")
    print(gbm_importance.head(10).to_string())

    print()
    baseline_importance = explain_baseline(features_df, out_dir)
    baseline_importance.to_csv(out_dir / "shap_baseline_importance.csv", header=["mean_abs_shap"])
    print("Logistic regression top features (mean |SHAP|):")
    print(baseline_importance.head(10).to_string())

    print(f"\nwrote plots + importance tables to {out_dir}/")
