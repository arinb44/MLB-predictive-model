"""FastAPI endpoint: given two team names and a date, returns a calibrated
home-team win probability.

Recomputes rolling features (team form, Elo, park factor, bullpen fatigue,
starter performance) for the requested game by appending it as a
hypothetical next game onto the cached historical game log and re-running
the same leakage-safe pipeline used for training (src/data/build_features.py,
src/models/elo.py) — not a separate, hand-rolled "look up the latest stat"
path that could quietly drift from what the model was actually trained on.
This recomputes across the full history on every request, which is fine for
a portfolio-scale demo but would need incremental/cached state to serve
real traffic.

Starting pitchers aren't knowable this far ahead of a future game (MLB
announces probables ~5 days out), so `home_pitcher_id`/`away_pitcher_id` in
the request are optional. Omitted, the request correctly falls back to the
same "unknown pitcher" embedding bucket and NaN numeric proxy used for any
other missing-starter case (e.g. 2024 games — see fetch_pitchers.py) rather
than guessing. Pass them for a same-day prediction once probables are known.

When pitcher IDs are provided, the response also includes their real
current-season Statcast quality metrics (`home_pitcher_stats`/
`away_pitcher_stats`, from fetch_statcast_leaderboard.py) — informational
only, NOT fed into the model. There's no leakage-safe historical version of
this data to train on (Baseball Savant's leaderboard endpoint only returns
full-season-to-date snapshots, not point-in-time history), and substituting
it into the model's existing `starter_runs_allowed_last{w}` feature would
mean feeding a differently-distributed value (earned-only, per-9-innings,
season-cumulative) into a slot calibrated on a noisier one (team total runs
per start) — see fetch_statcast_leaderboard.py for the full reasoning.
"""
import sys
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import List, Optional

import joblib
import pandas as pd
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.build_features import add_starter_features, build_game_features, merge_elo_features  # noqa: E402
from src.models.elo import compute_elo_ratings  # noqa: E402

_state: dict = {}
_STATIC_DIR = Path(__file__).resolve().parent / "static"


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_artifacts() -> None:
    cfg = load_config()
    processed_dir = Path(cfg["data"]["processed_dir"])

    artifact = joblib.load("models/production_model.joblib")
    _state["model"] = artifact["pipeline"]
    _state["feature_cols"] = artifact["feature_cols"]
    _state["game_log"] = pd.read_csv(processed_dir / "game_log.csv")
    _state["starters"] = pd.read_csv(processed_dir / "starters.csv")
    _state["cfg"] = cfg

    known_teams = set(_state["game_log"]["home_team"]) | set(_state["game_log"]["away_team"])
    _state["known_teams"] = known_teams

    # Optional: informational-only Statcast stats (see module docstring for
    # why these never reach the model). Missing files just mean the
    # response's pitcher/hitter_stats fields stay null and /roster/{team}
    # returns empty lists — run fetch_statcast_leaderboard.py and
    # fetch_rosters.py to populate them.
    leaderboard_path = processed_dir / "statcast_leaderboard.csv"
    if leaderboard_path.exists():
        leaderboard = pd.read_csv(leaderboard_path).set_index("pitcher_id")
        _state["pitcher_stats"] = leaderboard.to_dict(orient="index")
    else:
        _state["pitcher_stats"] = {}

    batters_path = processed_dir / "statcast_batters.csv"
    if batters_path.exists():
        batters = pd.read_csv(batters_path).set_index("player_id")
        _state["hitter_stats"] = batters.to_dict(orient="index")
    else:
        _state["hitter_stats"] = {}

    rosters_path = processed_dir / "rosters.csv"
    if rosters_path.exists():
        _state["rosters"] = pd.read_csv(rosters_path)
    else:
        _state["rosters"] = pd.DataFrame(columns=["team", "player_id", "player_name", "is_pitcher"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_artifacts()
    yield


app = FastAPI(title="MLB Game Outcome Predictor", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def ui() -> str:
    return (_STATIC_DIR / "index.html").read_text()


class PredictionRequest(BaseModel):
    home_team: str
    away_team: str
    game_date: Optional[date] = None  # defaults to today
    home_pitcher_id: Optional[str] = None  # Retrosheet ID; omit if unknown/not yet announced
    away_pitcher_id: Optional[str] = None
    home_hitter_ids: List[str] = Field(default_factory=list, max_length=3)
    away_hitter_ids: List[str] = Field(default_factory=list, max_length=3)


class PitcherStats(BaseModel):
    era: float
    win: int
    loss: int
    xwoba: float
    whiff_percent: float
    k_percent: float
    bb_percent: float


class HitterStats(BaseModel):
    name: str
    avg: float
    slg: float
    obp: float
    rbi: int
    runs: int
    woba: float


class TeamFormStats(BaseModel):
    """Recent-form numbers actually fed to the model (see build_features.py)
    — shown here so the UI's head-to-head view isn't just the pitcher/hitter
    cards, since these are what the prediction itself is grounded in."""
    win_pct_last10: Optional[float] = None
    runs_scored_last10: Optional[float] = None
    elo: Optional[float] = None


class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    game_date: date
    home_win_probability: float
    home_team_stats: TeamFormStats
    away_team_stats: TeamFormStats
    home_pitcher_stats: Optional[PitcherStats] = None
    away_pitcher_stats: Optional[PitcherStats] = None
    home_hitter_stats: List[HitterStats] = Field(default_factory=list)
    away_hitter_stats: List[HitterStats] = Field(default_factory=list)


class RosterPlayer(BaseModel):
    player_id: str
    name: str


class RosterResponse(BaseModel):
    team: str
    pitchers: List[RosterPlayer]
    hitters: List[RosterPlayer]


def _lookup_pitcher_stats(pitcher_id: Optional[str]) -> Optional[PitcherStats]:
    if pitcher_id is None:
        return None
    row = _state["pitcher_stats"].get(pitcher_id)
    if row is None:
        return None
    return PitcherStats(
        era=row["p_era"], win=int(row["p_win"]), loss=int(row["p_loss"]),
        xwoba=row["xwoba"], whiff_percent=row["whiff_percent"],
        k_percent=row["k_percent"], bb_percent=row["bb_percent"],
    )


def _lookup_hitter_stats(hitter_ids: List[str]) -> List[HitterStats]:
    stats = []
    for hitter_id in hitter_ids:
        row = _state["hitter_stats"].get(hitter_id)
        if row is None:
            continue
        stats.append(HitterStats(
            name=row["last_name, first_name"], avg=row["batting_avg"], slg=row["slg_percent"],
            obp=row["on_base_percent"], rbi=int(row["b_rbi"]), runs=int(row["r_run"]), woba=row["woba"],
        ))
    return stats


def _safe_float(value) -> Optional[float]:
    return None if pd.isna(value) else float(value)


def _predict(
    home_team: str, away_team: str, game_date: date,
    home_pitcher_id: Optional[str] = None, away_pitcher_id: Optional[str] = None,
) -> tuple[float, TeamFormStats, TeamFormStats]:
    game_log = _state["game_log"]
    cfg = _state["cfg"]

    for team in (home_team, away_team):
        if team not in _state["known_teams"]:
            raise HTTPException(status_code=400, detail=f"Unknown team code: {team!r}")

    game_date_str = game_date.strftime("%Y-%m-%d")
    if (
        (game_log["home_team"] == home_team) & (game_log["away_team"] == away_team) & (game_log["game_date"] == game_date_str)
    ).any():
        game_number = int(game_log.loc[
            (game_log["home_team"] == home_team) & (game_log["away_team"] == away_team) & (game_log["game_date"] == game_date_str),
            "game_number",
        ].max()) + 1
    else:
        game_number = 1

    hypothetical = pd.DataFrame([{
        "game_date": game_date_str,
        "game_number": game_number,
        "season": game_date.year,
        "home_team": home_team,
        "away_team": away_team,
        "home_score": float("nan"),
        "away_score": float("nan"),
        "home_win": float("nan"),
        "Inn": 9,  # placeholder — this game hasn't happened; Inn only affects *future* rows via shift(1)
    }])
    extended_log = pd.concat([game_log, hypothetical], ignore_index=True)

    # Starters aren't knowable this far ahead of a future game — if the
    # caller didn't pass them, this row's pitcher IDs stay NaN, and
    # add_starter_features falls back to the same "unknown pitcher"
    # handling used for any other missing-starter game (e.g. 2024).
    hypothetical_starter = pd.DataFrame([{
        "game_date": game_date_str, "game_number": game_number, "season": game_date.year,
        "home_team": home_team, "away_team": away_team,
        "home_pitcher_id": home_pitcher_id, "home_pitcher_name": None,
        "away_pitcher_id": away_pitcher_id, "away_pitcher_name": None,
    }])
    extended_starters = pd.concat([_state["starters"], hypothetical_starter], ignore_index=True)

    features_cfg = cfg["features"]
    features = build_game_features(
        extended_log, features_cfg["rolling_windows"],
        fatigue_days=features_cfg["bullpen_fatigue_days"], park_window=features_cfg["park_factor_window"],
    )
    elo_df = compute_elo_ratings(extended_log, cfg)
    features = merge_elo_features(features, elo_df)
    features = add_starter_features(features, extended_starters, features_cfg["starter_trailing_starts"])

    row = features[
        (features["home_team"] == home_team) & (features["away_team"] == away_team)
        & (features["game_date"] == game_date_str) & (features["game_number"] == game_number)
    ]
    if row.empty:
        raise HTTPException(status_code=500, detail="Failed to compute features for the requested game")

    X = row[_state["feature_cols"]]
    prob = _state["model"].predict_proba(X)[0, 1]

    r = row.iloc[0]
    home_stats = TeamFormStats(
        win_pct_last10=_safe_float(r.get("home_win_pct_last10")),
        runs_scored_last10=_safe_float(r.get("home_runs_scored_last10")),
        elo=_safe_float(r.get("home_elo_pre")),
    )
    away_stats = TeamFormStats(
        win_pct_last10=_safe_float(r.get("away_win_pct_last10")),
        runs_scored_last10=_safe_float(r.get("away_runs_scored_last10")),
        elo=_safe_float(r.get("away_elo_pre")),
    )
    return float(prob), home_stats, away_stats


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    game_date = request.game_date or date.today()
    prob, home_team_stats, away_team_stats = _predict(
        request.home_team, request.away_team, game_date,
        home_pitcher_id=request.home_pitcher_id, away_pitcher_id=request.away_pitcher_id,
    )
    return PredictionResponse(
        home_team=request.home_team, away_team=request.away_team, game_date=game_date, home_win_probability=prob,
        home_team_stats=home_team_stats, away_team_stats=away_team_stats,
        home_pitcher_stats=_lookup_pitcher_stats(request.home_pitcher_id),
        away_pitcher_stats=_lookup_pitcher_stats(request.away_pitcher_id),
        home_hitter_stats=_lookup_hitter_stats(request.home_hitter_ids),
        away_hitter_stats=_lookup_hitter_stats(request.away_hitter_ids),
    )


@app.get("/teams", response_model=List[str])
def teams() -> List[str]:
    return sorted(_state["known_teams"])


@app.get("/roster/{team}", response_model=RosterResponse)
def roster(team: str) -> RosterResponse:
    if team not in _state["known_teams"]:
        raise HTTPException(status_code=400, detail=f"Unknown team code: {team!r}")

    team_roster = _state["rosters"][_state["rosters"]["team"] == team]
    pitchers = team_roster[team_roster["is_pitcher"]]
    hitters = team_roster[~team_roster["is_pitcher"]]
    return RosterResponse(
        team=team,
        pitchers=[RosterPlayer(player_id=r.player_id, name=r.player_name) for r in pitchers.itertuples()],
        hitters=[RosterPlayer(player_id=r.player_id, name=r.player_name) for r in hitters.itertuples()],
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": "model" in _state}
