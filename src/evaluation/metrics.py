"""Sports-outcome models are judged on calibration, not just accuracy — a
model saying "60%" should be right ~60% of the time across all such calls.
log-loss and Brier score both penalize confident wrong predictions far more
than accuracy does, which is why they're the primary metrics here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss


def evaluate_predictions(y_true, y_prob) -> dict:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    return {
        "log_loss": log_loss(y_true, y_prob, labels=[0, 1]),
        "brier_score": brier_score_loss(y_true, y_prob),
        "accuracy": ((y_prob > 0.5).astype(int) == y_true).mean(),
        "n": len(y_true),
    }


def calibration_table(y_true, y_prob, n_bins: int = 10) -> pd.DataFrame:
    """Bucket predictions into probability bins and compare predicted vs.
    actual win rate per bin — the data behind a calibration plot. A
    well-calibrated model has predicted_mean ~= actual_rate in every bin.
    """
    df = pd.DataFrame({"y_true": np.asarray(y_true), "y_prob": np.asarray(y_prob)})
    df["bin"] = pd.cut(df["y_prob"], bins=np.linspace(0, 1, n_bins + 1), include_lowest=True)

    table = df.groupby("bin", observed=True).agg(
        predicted_mean=("y_prob", "mean"),
        actual_rate=("y_true", "mean"),
        n=("y_true", "size"),
    ).reset_index()
    return table


def plot_calibration(y_true, y_prob, n_bins: int = 10, ax=None, label: str | None = None):
    import matplotlib.pyplot as plt

    table = calibration_table(y_true, y_prob, n_bins)

    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))

    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfectly calibrated")
    ax.plot(table["predicted_mean"], table["actual_rate"], marker="o", label=label or "model")
    ax.set_xlabel("predicted win probability")
    ax.set_ylabel("actual win rate")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    return ax
