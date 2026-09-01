"""Dataset for the entity-embedding model: team and starting-pitcher IDs
encoded to integer indices (for nn.Embedding), numeric rolling-form/Elo/
starter features imputed and standardized. Imputation/scaling statistics
are fit once (on a training split) and reused everywhere else, the same
discipline as the sklearn Pipeline in baseline.py — a val/test split must
never influence the stats used to transform it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class CategoricalEncoder:
    """Label-encodes a categorical ID column (team abbreviation, pitcher ID,
    ...) to embedding indices. Fit only on training-split values; anything
    not seen during fit — an unseen team, or a missing pitcher ID (e.g. 2024
    games, which have no Retrosheet-sourced starter yet) — maps to a
    reserved "unknown" index rather than raising.
    """

    def __init__(self):
        self.value_to_idx: dict[str, int] = {}
        self.unknown_idx: int = 0

    def fit(self, values: pd.Series) -> "CategoricalEncoder":
        unique_values = sorted(values.dropna().unique())
        self.value_to_idx = {v: i for i, v in enumerate(unique_values)}
        self.unknown_idx = len(self.value_to_idx)
        return self

    @property
    def num_classes(self) -> int:
        return len(self.value_to_idx) + 1  # +1 for the unknown bucket

    def transform(self, values: pd.Series) -> np.ndarray:
        return values.map(lambda v: self.value_to_idx.get(v, self.unknown_idx)).to_numpy()


class GameDataset(Dataset):
    def __init__(
        self,
        df: pd.DataFrame,
        numeric_cols: list[str],
        team_encoder: CategoricalEncoder,
        pitcher_encoder: CategoricalEncoder,
        numeric_mean: np.ndarray | None = None,
        numeric_std: np.ndarray | None = None,
    ):
        self.home_team_idx = torch.as_tensor(team_encoder.transform(df["home_team"]), dtype=torch.long)
        self.away_team_idx = torch.as_tensor(team_encoder.transform(df["away_team"]), dtype=torch.long)
        self.home_pitcher_idx = torch.as_tensor(pitcher_encoder.transform(df["home_pitcher_id"]), dtype=torch.long)
        self.away_pitcher_idx = torch.as_tensor(pitcher_encoder.transform(df["away_pitcher_id"]), dtype=torch.long)

        raw = df[numeric_cols].to_numpy(dtype=np.float32)

        # Fit imputation/scaling stats only when not supplied (i.e. on the
        # training split) — nanmean/nanstd so early-season NaN rows don't
        # poison the statistics themselves.
        if numeric_mean is None:
            numeric_mean = np.nanmean(raw, axis=0)
            filled = np.where(np.isnan(raw), numeric_mean, raw)
            numeric_std = filled.std(axis=0)
            numeric_std[numeric_std == 0] = 1.0

        filled = np.where(np.isnan(raw), numeric_mean, raw)
        numeric = (filled - numeric_mean) / numeric_std

        self.numeric_mean = numeric_mean
        self.numeric_std = numeric_std
        self.numeric = torch.as_tensor(numeric, dtype=torch.float32)
        # At pure-inference time (TorchModelWrapper.predict_proba) the caller
        # only has feature columns, no label — the returned y is unused in
        # that path (see _predict_proba_array), so a zero placeholder is fine.
        if "home_win" in df.columns:
            self.y = torch.as_tensor(df["home_win"].to_numpy(dtype=np.float32))
        else:
            self.y = torch.zeros(len(df), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx):
        return (
            self.home_team_idx[idx], self.away_team_idx[idx],
            self.home_pitcher_idx[idx], self.away_pitcher_idx[idx],
            self.numeric[idx], self.y[idx],
        )
