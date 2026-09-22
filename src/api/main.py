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
from src.data.teams import TEAMS, logo_url  # noqa: E402
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

    # Optional: informational-only season stats for the UI's Players/Teams
    # views (fetch_player_war.py, fetch_team_stats.py). Missing files mean
    # /stats/players and /stats/teams return empty lists.
    _state["player_stats"] = _build_player_stats(processed_dir)
    team_stats_path = processed_dir / "team_stats.csv"
    _state["team_stats"] = pd.read_csv(team_stats_path) if team_stats_path.exists() else pd.DataFrame()


# Statcast leaderboard column -> player stats field, joined onto the WAR rows
# by MLBAM ID so the Players view can plot contact quality next to WAR.
_STATCAST_HITTER_COLS = {
    "batting_avg": "avg", "on_base_percent": "obp", "slg_percent": "slg", "b_rbi": "rbi", "r_run": "runs",
    "woba": "woba", "xwoba": "xwoba", "k_percent": "k_percent", "bb_percent": "bb_percent",
    "hard_hit_percent": "hard_hit_percent", "barrel_batted_rate": "barrel_percent",
}
_STATCAST_PITCHER_COLS = {
    "p_era": "era", "p_win": "wins", "p_loss": "losses", "xwoba": "xwoba_against",
    "k_percent": "k_percent", "bb_percent": "bb_percent", "whiff_percent": "whiff_percent",
    "hard_hit_percent": "hard_hit_percent", "barrel_batted_rate": "barrel_percent",
}


def _build_player_stats(processed_dir: Path) -> pd.DataFrame:
    war_path = processed_dir / "player_war.csv"
    if not war_path.exists():
        return pd.DataFrame()
    war = pd.read_csv(war_path)
    parts = []
    for role, filename, cols in (
        ("hitter", "statcast_batters.csv", _STATCAST_HITTER_COLS),
        ("pitcher", "statcast_leaderboard.csv", _STATCAST_PITCHER_COLS),
    ):
        part = war[war["role"] == role]
        statcast_path = processed_dir / filename
        if statcast_path.exists():
            statcast = pd.read_csv(statcast_path)[["key_mlbam", *cols]].rename(columns=cols)
            statcast = statcast.drop_duplicates("key_mlbam").rename(columns={"key_mlbam": "mlb_id"})
            part = part.merge(statcast, on="mlb_id", how="left")
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame rows as dicts with NaN -> None, so they serialize as JSON null."""
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


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


class TeamMeta(BaseModel):
    team: str
    name: str
    league: str
    division: str
    color: str
    logo_url: str


class PlayerStatLine(BaseModel):
    """One player's season line for the Players view. Hitter-only fields are
    null for pitchers and vice versa; Statcast fields are null when the
    player isn't on that leaderboard. Informational only — never a model input."""
    mlb_id: int
    player_name: str
    role: str
    team: str
    age: Optional[float] = None
    war: Optional[float] = None
    games: Optional[int] = None
    # hitters (Baseball-Reference)
    war_off: Optional[float] = None
    war_def: Optional[float] = None
    pa: Optional[int] = None
    ops_plus: Optional[float] = None
    runs_bat: Optional[float] = None
    runs_field: Optional[float] = None
    # hitters (Statcast)
    avg: Optional[float] = None
    obp: Optional[float] = None
    slg: Optional[float] = None
    rbi: Optional[int] = None
    runs: Optional[int] = None
    woba: Optional[float] = None
    xwoba: Optional[float] = None
    # pitchers (Baseball-Reference)
    games_started: Optional[int] = None
    ip: Optional[float] = None
    era_plus: Optional[float] = None
    # pitchers (Statcast)
    era: Optional[float] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    xwoba_against: Optional[float] = None
    whiff_percent: Optional[float] = None
    # both roles (Statcast)
    k_percent: Optional[float] = None
    bb_percent: Optional[float] = None
    hard_hit_percent: Optional[float] = None
    barrel_percent: Optional[float] = None


class TeamStatLine(BaseModel):
    """One team's season line for the Teams view. `ops_plus` is the UI's
    "offensive rating" (see fetch_team_stats.py). Informational only."""
    team: str
    games: int
    wins: int
    losses: int
    runs: int
    runs_allowed: int
    runs_per_game: float
    runs_allowed_per_game: float
    run_diff: int
    avg: float
    obp: float
    slg: float
    ops: float
    home_runs: int
    stolen_bases: int
    k_percent: float
    bb_percent: float
    era: float
    whip: float
    k_per_9: float
    bb_per_9: float
    hr_allowed: int
    ops_plus: Optional[float] = None
    hitter_war: Optional[float] = None
    pitcher_war: Optional[float] = None
    total_war: Optional[float] = None
    offense_runs_above_avg: Optional[float] = None


@app.get("/teams/meta", response_model=List[TeamMeta])
def teams_meta() -> List[TeamMeta]:
    return [
        TeamMeta(team=code, name=meta["name"], league=meta["league"], division=meta["division"],
                 color=meta["color"], logo_url=logo_url(code))
        for code, meta in sorted(TEAMS.items())
    ]


@app.get("/stats/players", response_model=List[PlayerStatLine])
def player_stats(role: Optional[str] = None, team: Optional[str] = None) -> List[PlayerStatLine]:
    if role is not None and role not in ("hitter", "pitcher"):
        raise HTTPException(status_code=400, detail="role must be 'hitter' or 'pitcher'")
    if team is not None and team not in TEAMS:
        raise HTTPException(status_code=400, detail=f"Unknown team code: {team!r}")
    df = _state["player_stats"]
    if df.empty:
        return []
    if role is not None:
        df = df[df["role"] == role]
    if team is not None:
        df = df[df["team"] == team]
    return [PlayerStatLine(**r) for r in _records(df)]


@app.get("/stats/teams", response_model=List[TeamStatLine])
def team_stats() -> List[TeamStatLine]:
    return [TeamStatLine(**r) for r in _records(_state["team_stats"])]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": "model" in _state}
