"""API-level tests using FastAPI's TestClient — a real gap before this file
existed: every other test covered the leakage-safe feature/Elo logic, but
nothing exercised the serving layer itself (routing, request validation,
the informational-only guarantees the README makes about pitcher/hitter
stats never reaching the model).

Requires the same artifacts the API needs to actually start
(data/processed/game_log.csv, starters.csv, models/production_model.joblib)
— these are gitignored/regenerated, not checked in, so this suite only runs
where the pipeline has already been run at least once (see README).
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.main import app  # noqa: E402

_REQUIRED_ARTIFACTS = [
    "data/processed/game_log.csv",
    "data/processed/starters.csv",
    "models/production_model.joblib",
]


@pytest.fixture(scope="module")
def client():
    missing = [p for p in _REQUIRED_ARTIFACTS if not Path(p).exists()]
    if missing:
        pytest.skip(f"API artifacts not built yet, skipping API tests: {missing} — see README's 'Reproducing the pipeline'")

    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "model_loaded": True}


def test_ui_served_at_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "MLB Game Outcome Predictor" in resp.text


def test_teams_lists_all_30(client):
    resp = client.get("/teams")
    assert resp.status_code == 200
    teams = resp.json()
    assert len(teams) == 30
    assert "NYY" in teams and "BOS" in teams


def test_roster_known_team_has_expected_shape(client):
    resp = client.get("/roster/NYY")
    assert resp.status_code == 200
    body = resp.json()
    assert body["team"] == "NYY"
    assert "pitchers" in body and "hitters" in body
    for group in (body["pitchers"], body["hitters"]):
        for player in group:
            assert set(player.keys()) == {"player_id", "name"}


def test_roster_unknown_team_is_400(client):
    resp = client.get("/roster/ZZZ")
    assert resp.status_code == 400


def test_predict_basic_returns_valid_probability(client):
    resp = client.post("/predict", json={"home_team": "NYY", "away_team": "BOS"})
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["home_win_probability"] <= 1.0
    assert body["home_pitcher_stats"] is None
    assert body["home_hitter_stats"] == []


def test_predict_unknown_team_is_400(client):
    resp = client.post("/predict", json={"home_team": "ZZZ", "away_team": "BOS"})
    assert resp.status_code == 400


def test_predict_same_team_home_and_away_is_not_rejected_by_api(client):
    """The API itself doesn't forbid this (only the web UI's JS does) — it's
    a well-defined, if unrealistic, hypothetical game and should still
    return a valid probability rather than erroring."""
    resp = client.post("/predict", json={"home_team": "NYY", "away_team": "NYY"})
    assert resp.status_code == 200
    assert 0.0 <= resp.json()["home_win_probability"] <= 1.0


def test_predict_more_than_three_hitters_is_rejected(client):
    resp = client.post("/predict", json={
        "home_team": "NYY", "away_team": "BOS",
        "home_hitter_ids": ["a", "b", "c", "d"],
    })
    assert resp.status_code == 422


def test_unknown_pitcher_id_falls_back_identically_to_omitted(client):
    """Proves the API's documented fallback behavior: a pitcher ID that
    doesn't match anything must produce byte-identical predictions to not
    passing one at all, rather than silently doing something else."""
    omitted = client.post("/predict", json={"home_team": "NYY", "away_team": "BOS"})
    unknown = client.post("/predict", json={
        "home_team": "NYY", "away_team": "BOS", "home_pitcher_id": "not_a_real_pitcher_id",
    })
    assert omitted.json()["home_win_probability"] == unknown.json()["home_win_probability"]
    assert unknown.json()["home_pitcher_stats"] is None


def test_hitter_selection_does_not_change_win_probability(client):
    """The core informational-only guarantee: whatever hitters are passed,
    they must never move the model's prediction, only the display fields.
    """
    roster = client.get("/roster/NYY").json()
    if not roster["hitters"]:
        pytest.skip("no NYY hitters available in this environment's rosters.csv")

    without_hitters = client.post("/predict", json={"home_team": "NYY", "away_team": "BOS"})
    hitter_id = roster["hitters"][0]["player_id"]
    with_hitters = client.post("/predict", json={
        "home_team": "NYY", "away_team": "BOS", "home_hitter_ids": [hitter_id],
    })

    assert without_hitters.json()["home_win_probability"] == with_hitters.json()["home_win_probability"]
    assert len(with_hitters.json()["home_hitter_stats"]) == 1


def test_teams_meta_covers_every_team_with_a_logo(client):
    resp = client.get("/teams/meta")
    assert resp.status_code == 200
    meta = resp.json()
    assert {m["team"] for m in meta} == set(client.get("/teams").json())
    for m in meta:
        assert m["logo_url"].startswith("https://www.mlbstatic.com/team-logos/")


def test_player_stats_filters_by_role_and_team(client):
    if not Path("data/processed/player_war.csv").exists():
        pytest.skip("player_war.csv not built — run src.data.fetch_player_war")
    resp = client.get("/stats/players", params={"role": "hitter", "team": "NYY"})
    assert resp.status_code == 200
    players = resp.json()
    assert players
    assert all(p["role"] == "hitter" and p["team"] == "NYY" for p in players)
    assert all(p["ip"] is None for p in players)


def test_player_stats_rejects_bad_filters(client):
    assert client.get("/stats/players", params={"role": "catcher"}).status_code == 400
    assert client.get("/stats/players", params={"team": "ZZZ"}).status_code == 400


def test_team_stats_has_all_30_teams(client):
    if not Path("data/processed/team_stats.csv").exists():
        pytest.skip("team_stats.csv not built — run src.data.fetch_team_stats")
    resp = client.get("/stats/teams")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 30
    assert {r["team"] for r in rows} == set(client.get("/teams").json())
