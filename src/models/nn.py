"""Entity-embedding model: nn.Embedding for team AND starting-pitcher
identity, concatenated with the same numeric rolling-form/Elo/starter
features used by the GBM, through a small MLP head. This is the idea
one-hot encoding / boosted trees can't capture as naturally — the model
learns dense representations of "what kind of team is the Dodgers" and
"what kind of pitcher is Kershaw" rather than treating either identity as
an unordered category. Pitcher identity is the highest-cardinality input in
this project (thousands of distinct starters vs. 30 teams), which is
exactly where embeddings should have the most room to add value.

Training loop is hand-written (not PyTorch Lightning) so the mechanics —
optimizer step, loss, backward pass — stay visible.

Chronological discipline: this module only shuffles rows *within* whatever
split it's given (DataLoader(shuffle=True) below applies only to the
training loader). The walk-forward harness in evaluation/backtest.py is what
enforces that no season used for training comes after the test season.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.models.baseline import NON_FEATURE_COLS
from src.models.torch_dataset import CategoricalEncoder, GameDataset

TEAM_COLS = ["home_team", "away_team"]
PITCHER_COLS = ["home_pitcher_id", "away_pitcher_id"]
CATEGORICAL_COLS = TEAM_COLS + PITCHER_COLS


def get_feature_columns(features_df: pd.DataFrame) -> list[str]:
    numeric_cols = [c for c in features_df.columns if c not in NON_FEATURE_COLS]
    return CATEGORICAL_COLS + numeric_cols


class EntityEmbeddingNet(nn.Module):
    def __init__(
        self,
        num_teams: int,
        num_pitchers: int,
        num_numeric: int,
        team_embedding_dim: int = 8,
        pitcher_embedding_dim: int = 8,
        hidden_dims: tuple[int, ...] = (64, 32),
        dropout: float = 0.2,
    ):
        super().__init__()
        self.team_embedding = nn.Embedding(num_teams, team_embedding_dim)
        self.pitcher_embedding = nn.Embedding(num_pitchers, pitcher_embedding_dim)

        # home + away team embeddings, home + away pitcher embeddings, numeric features
        input_dim = team_embedding_dim * 2 + pitcher_embedding_dim * 2 + num_numeric
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers += [nn.Linear(prev_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout)]
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))
        self.mlp = nn.Sequential(*layers)

    def forward(
        self, home_team_idx: torch.Tensor, away_team_idx: torch.Tensor,
        home_pitcher_idx: torch.Tensor, away_pitcher_idx: torch.Tensor, numeric: torch.Tensor,
    ) -> torch.Tensor:
        home_team_emb = self.team_embedding(home_team_idx)
        away_team_emb = self.team_embedding(away_team_idx)
        home_pitcher_emb = self.pitcher_embedding(home_pitcher_idx)
        away_pitcher_emb = self.pitcher_embedding(away_pitcher_idx)
        x = torch.cat([home_team_emb, away_team_emb, home_pitcher_emb, away_pitcher_emb, numeric], dim=1)
        return self.mlp(x).squeeze(-1)  # logits, BCEWithLogitsLoss applies the sigmoid


def run_training_loop(
    model: EntityEmbeddingNet,
    train_loader: DataLoader,
    val_loader: DataLoader | None = None,
    lr: float = 1e-3,
    epochs: int = 30,
    device: str = "cpu",
    verbose: bool = False,
) -> list[dict]:
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCEWithLogitsLoss()

    history = []
    for epoch in range(epochs):
        model.train()
        train_loss, n = 0.0, 0
        for home_team_idx, away_team_idx, home_pitcher_idx, away_pitcher_idx, numeric, y in train_loader:
            home_team_idx, away_team_idx = home_team_idx.to(device), away_team_idx.to(device)
            home_pitcher_idx, away_pitcher_idx = home_pitcher_idx.to(device), away_pitcher_idx.to(device)
            numeric, y = numeric.to(device), y.to(device)

            optimizer.zero_grad()
            logits = model(home_team_idx, away_team_idx, home_pitcher_idx, away_pitcher_idx, numeric)
            loss = loss_fn(logits, y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(y)
            n += len(y)
        train_loss /= n

        val_loss = _evaluate_loss(model, val_loader, loss_fn, device) if val_loader is not None else None
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        if verbose:
            msg = f"epoch {epoch + 1}/{epochs}  train_loss={train_loss:.4f}"
            if val_loss is not None:
                msg += f"  val_loss={val_loss:.4f}"
            print(msg)

    return history


@torch.no_grad()
def _evaluate_loss(model: EntityEmbeddingNet, loader: DataLoader, loss_fn, device: str) -> float:
    model.eval()
    total_loss, n = 0.0, 0
    for home_team_idx, away_team_idx, home_pitcher_idx, away_pitcher_idx, numeric, y in loader:
        home_team_idx, away_team_idx = home_team_idx.to(device), away_team_idx.to(device)
        home_pitcher_idx, away_pitcher_idx = home_pitcher_idx.to(device), away_pitcher_idx.to(device)
        numeric, y = numeric.to(device), y.to(device)
        loss = loss_fn(model(home_team_idx, away_team_idx, home_pitcher_idx, away_pitcher_idx, numeric), y)
        total_loss += loss.item() * len(y)
        n += len(y)
    return total_loss / n


@torch.no_grad()
def _predict_proba_array(model: EntityEmbeddingNet, loader: DataLoader, device: str) -> np.ndarray:
    model.eval()
    probs = []
    for home_team_idx, away_team_idx, home_pitcher_idx, away_pitcher_idx, numeric, _y in loader:
        home_team_idx, away_team_idx = home_team_idx.to(device), away_team_idx.to(device)
        home_pitcher_idx, away_pitcher_idx = home_pitcher_idx.to(device), away_pitcher_idx.to(device)
        numeric = numeric.to(device)
        logits = model(home_team_idx, away_team_idx, home_pitcher_idx, away_pitcher_idx, numeric)
        probs.append(torch.sigmoid(logits).cpu().numpy())
    return np.concatenate(probs)


class TorchModelWrapper:
    """sklearn-style adapter (.predict_proba(X) -> (n, 2)) so the entity-
    embedding model plugs into the same walk-forward harness as the
    logistic regression baseline and GBM."""

    def __init__(
        self, model: EntityEmbeddingNet, team_encoder: CategoricalEncoder, pitcher_encoder: CategoricalEncoder,
        numeric_cols: list[str], numeric_mean: np.ndarray, numeric_std: np.ndarray,
        batch_size: int = 256, device: str = "cpu",
    ):
        self.model = model
        self.team_encoder = team_encoder
        self.pitcher_encoder = pitcher_encoder
        self.numeric_cols = numeric_cols
        self.numeric_mean = numeric_mean
        self.numeric_std = numeric_std
        self.batch_size = batch_size
        self.device = device

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        dataset = GameDataset(
            X, self.numeric_cols, self.team_encoder, self.pitcher_encoder,
            numeric_mean=self.numeric_mean, numeric_std=self.numeric_std,
        )
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        probs = _predict_proba_array(self.model, loader, self.device)
        return np.stack([1 - probs, probs], axis=1)


def train(
    train_df: pd.DataFrame,
    feature_cols: list[str],
    team_embedding_dim: int = 8,
    pitcher_embedding_dim: int = 8,
    hidden_dims: tuple[int, ...] = (64, 32),
    dropout: float = 0.2,
    lr: float = 1e-3,
    batch_size: int = 256,
    epochs: int = 30,
    device: str = "cpu",
    verbose: bool = False,
) -> TorchModelWrapper:
    numeric_cols = [c for c in feature_cols if c not in CATEGORICAL_COLS]

    team_encoder = CategoricalEncoder().fit(pd.concat([train_df["home_team"], train_df["away_team"]]))
    pitcher_encoder = CategoricalEncoder().fit(pd.concat([train_df["home_pitcher_id"], train_df["away_pitcher_id"]]))
    train_dataset = GameDataset(train_df, numeric_cols, team_encoder, pitcher_encoder)
    # shuffle=True is safe here: it only shuffles *within* this training
    # fold, which the caller has already restricted to seasons before the
    # held-out test season.
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    model = EntityEmbeddingNet(
        num_teams=team_encoder.num_classes, num_pitchers=pitcher_encoder.num_classes, num_numeric=len(numeric_cols),
        team_embedding_dim=team_embedding_dim, pitcher_embedding_dim=pitcher_embedding_dim,
        hidden_dims=hidden_dims, dropout=dropout,
    )
    run_training_loop(model, train_loader, lr=lr, epochs=epochs, device=device, verbose=verbose)

    return TorchModelWrapper(
        model, team_encoder, pitcher_encoder, numeric_cols,
        train_dataset.numeric_mean, train_dataset.numeric_std, batch_size=batch_size, device=device,
    )


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    import yaml

    parser = argparse.ArgumentParser(description="Fit the entity-embedding model on all available data (no holdout).")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    processed_dir = Path(cfg["data"]["processed_dir"])
    features_df = pd.read_csv(processed_dir / "features.csv")
    feature_cols = get_feature_columns(features_df)

    nn_cfg = cfg["model"]["nn"]
    wrapper = train(
        features_df, feature_cols,
        team_embedding_dim=nn_cfg["team_embedding_dim"], pitcher_embedding_dim=nn_cfg["pitcher_embedding_dim"],
        hidden_dims=tuple(nn_cfg["hidden_dims"]), dropout=nn_cfg["dropout"],
        lr=nn_cfg["lr"], batch_size=nn_cfg["batch_size"], epochs=nn_cfg["epochs"], verbose=True,
    )
    print("trained entity-embedding model")
