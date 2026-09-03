FROM python:3.11-slim

WORKDIR /app

# Install deps first so this layer stays cached across code-only changes.
COPY requirements.txt .
# torch's default PyPI wheel on Linux pulls ~7GB of NVIDIA CUDA packages
# that go entirely unused here (this container has no GPU and only ever
# does CPU inference). Installing the CPU-only build first means the
# torch==... pin in requirements.txt below is already satisfied, so pip
# skips reinstalling it — this is what actually avoids the CUDA pull rather
# than a --no-deps flag, which would risk silently dropping a real
# dependency of torch.
RUN pip install --no-cache-dir torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY config.yaml .

# The API only needs the historical game log + starter identity (to compute
# rolling features for a requested game on the fly) and the fitted
# production model — not raw pulls, notebooks, or the other intermediate
# processed files. Regenerate these outside Docker with:
#   python -m src.data.fetch && python -m src.data.fetch_pitchers && python -m src.models.elo && python -m src.data.build_features && python scripts/train.py
COPY data/processed/game_log.csv data/processed/game_log.csv
COPY data/processed/starters.csv data/processed/starters.csv
COPY models/production_model.joblib models/production_model.joblib

# Optional — informational-only Statcast pitcher/batter stats, the web
# UI's team-roster dropdowns, and the Players/Teams tabs' season stats (see
# src/api/main.py, fetch_statcast_leaderboard.py, fetch_rosters.py,
# fetch_player_war.py, fetch_team_stats.py). The API starts fine without
# these (pitcher/hitter_stats fields stay null, /roster/{team} and
# /stats/* return empty lists). The trailing `*` makes each an optional glob
# copy — unlike an exact filename, Docker doesn't fail the build if nothing
# matches. Refresh with:
#   python -m src.data.fetch_statcast_leaderboard && python -m src.data.fetch_rosters
#   python -m src.data.fetch_player_war && python -m src.data.fetch_team_stats
COPY data/processed/statcast_leaderboard.csv* data/processed/
COPY data/processed/statcast_batters.csv* data/processed/
COPY data/processed/rosters.csv* data/processed/
COPY data/processed/player_war.csv* data/processed/
COPY data/processed/team_stats.csv* data/processed/

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
