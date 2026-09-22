"""Static per-team metadata keyed by the Baseball-Reference team codes used
everywhere else in this project (game_log.csv, rosters.csv, the WAR files).

`mlb_id` is MLB's official team ID — it's what the MLB Stats API returns
(fetch_team_stats.py joins on it) and what MLB's public logo CDN is keyed
by, so the web UI builds logo URLs from it rather than vendoring image files.

Baseball-Reference switched the Athletics' code from OAK to ATH starting in
2025 (the move out of Oakland); the historical game log still says OAK, so
OAK stays the canonical code here and ATH is mapped onto it on ingest.

`city` and `ballpark` are display-only (the matchup card's labels); ballparks
are current as of the 2026 season (the Athletics play in Sacramento through
2027, the Rays back at Tropicana Field after the 2025 season in Tampa).
"""

# The "on-dark" variant: the default logos use each team's dark primary
# color (e.g. Yankees navy), which disappears against the UI's dark theme.
LOGO_URL = "https://www.mlbstatic.com/team-logos/team-cap-on-dark/{mlb_id}.svg"
# Full primary mark (vs. the compact cap logo above) — used large, e.g. the
# faded logos on the prediction matchup card.
PRIMARY_LOGO_URL = "https://www.mlbstatic.com/team-logos/team-primary-on-dark/{mlb_id}.svg"

TEAMS = {
    "ARI": {"mlb_id": 109, "name": "Arizona Diamondbacks", "league": "NL", "division": "NL West", "color": "#A71930",
            "city": "Arizona", "ballpark": "Chase Field · Phoenix, AZ"},
    "ATL": {"mlb_id": 144, "name": "Atlanta Braves", "league": "NL", "division": "NL East", "color": "#CE1141",
            "city": "Atlanta", "ballpark": "Truist Park · Atlanta, GA"},
    "BAL": {"mlb_id": 110, "name": "Baltimore Orioles", "league": "AL", "division": "AL East", "color": "#DF4601",
            "city": "Baltimore", "ballpark": "Camden Yards · Baltimore, MD"},
    "BOS": {"mlb_id": 111, "name": "Boston Red Sox", "league": "AL", "division": "AL East", "color": "#BD3039",
            "city": "Boston", "ballpark": "Fenway Park · Boston, MA"},
    "CHC": {"mlb_id": 112, "name": "Chicago Cubs", "league": "NL", "division": "NL Central", "color": "#0E3386",
            "city": "Chicago", "ballpark": "Wrigley Field · Chicago, IL"},
    "CHW": {"mlb_id": 145, "name": "Chicago White Sox", "league": "AL", "division": "AL Central", "color": "#27251F",
            "city": "Chicago", "ballpark": "Rate Field · Chicago, IL"},
    "CIN": {"mlb_id": 113, "name": "Cincinnati Reds", "league": "NL", "division": "NL Central", "color": "#C6011F",
            "city": "Cincinnati", "ballpark": "Great American Ball Park · Cincinnati, OH"},
    "CLE": {"mlb_id": 114, "name": "Cleveland Guardians", "league": "AL", "division": "AL Central", "color": "#00385D",
            "city": "Cleveland", "ballpark": "Progressive Field · Cleveland, OH"},
    "COL": {"mlb_id": 115, "name": "Colorado Rockies", "league": "NL", "division": "NL West", "color": "#333366",
            "city": "Colorado", "ballpark": "Coors Field · Denver, CO"},
    "DET": {"mlb_id": 116, "name": "Detroit Tigers", "league": "AL", "division": "AL Central", "color": "#0C2340",
            "city": "Detroit", "ballpark": "Comerica Park · Detroit, MI"},
    "HOU": {"mlb_id": 117, "name": "Houston Astros", "league": "AL", "division": "AL West", "color": "#EB6E1F",
            "city": "Houston", "ballpark": "Daikin Park · Houston, TX"},
    "KCR": {"mlb_id": 118, "name": "Kansas City Royals", "league": "AL", "division": "AL Central", "color": "#004687",
            "city": "Kansas City", "ballpark": "Kauffman Stadium · Kansas City, MO"},
    "LAA": {"mlb_id": 108, "name": "Los Angeles Angels", "league": "AL", "division": "AL West", "color": "#BA0021",
            "city": "Los Angeles", "ballpark": "Angel Stadium · Anaheim, CA"},
    "LAD": {"mlb_id": 119, "name": "Los Angeles Dodgers", "league": "NL", "division": "NL West", "color": "#005A9C",
            "city": "Los Angeles", "ballpark": "Dodger Stadium · Los Angeles, CA"},
    "MIA": {"mlb_id": 146, "name": "Miami Marlins", "league": "NL", "division": "NL East", "color": "#00A3E0",
            "city": "Miami", "ballpark": "loanDepot park · Miami, FL"},
    "MIL": {"mlb_id": 158, "name": "Milwaukee Brewers", "league": "NL", "division": "NL Central", "color": "#12284B",
            "city": "Milwaukee", "ballpark": "American Family Field · Milwaukee, WI"},
    "MIN": {"mlb_id": 142, "name": "Minnesota Twins", "league": "AL", "division": "AL Central", "color": "#002B5C",
            "city": "Minnesota", "ballpark": "Target Field · Minneapolis, MN"},
    "NYM": {"mlb_id": 121, "name": "New York Mets", "league": "NL", "division": "NL East", "color": "#FF5910",
            "city": "New York", "ballpark": "Citi Field · Queens, NY"},
    "NYY": {"mlb_id": 147, "name": "New York Yankees", "league": "AL", "division": "AL East", "color": "#0C2340",
            "city": "New York", "ballpark": "Yankee Stadium · Bronx, NY"},
    "OAK": {"mlb_id": 133, "name": "Athletics", "league": "AL", "division": "AL West", "color": "#003831",
            "city": "Sacramento", "ballpark": "Sutter Health Park · Sacramento, CA"},
    "PHI": {"mlb_id": 143, "name": "Philadelphia Phillies", "league": "NL", "division": "NL East", "color": "#E81828",
            "city": "Philadelphia", "ballpark": "Citizens Bank Park · Philadelphia, PA"},
    "PIT": {"mlb_id": 134, "name": "Pittsburgh Pirates", "league": "NL", "division": "NL Central", "color": "#FDB827",
            "city": "Pittsburgh", "ballpark": "PNC Park · Pittsburgh, PA"},
    "SDP": {"mlb_id": 135, "name": "San Diego Padres", "league": "NL", "division": "NL West", "color": "#2F241D",
            "city": "San Diego", "ballpark": "Petco Park · San Diego, CA"},
    "SEA": {"mlb_id": 136, "name": "Seattle Mariners", "league": "AL", "division": "AL West", "color": "#0C2C56",
            "city": "Seattle", "ballpark": "T-Mobile Park · Seattle, WA"},
    "SFG": {"mlb_id": 137, "name": "San Francisco Giants", "league": "NL", "division": "NL West", "color": "#FD5A1E",
            "city": "San Francisco", "ballpark": "Oracle Park · San Francisco, CA"},
    "STL": {"mlb_id": 138, "name": "St. Louis Cardinals", "league": "NL", "division": "NL Central", "color": "#C41E3A",
            "city": "St. Louis", "ballpark": "Busch Stadium · St. Louis, MO"},
    "TBR": {"mlb_id": 139, "name": "Tampa Bay Rays", "league": "AL", "division": "AL East", "color": "#092C5C",
            "city": "Tampa Bay", "ballpark": "Tropicana Field · St. Petersburg, FL"},
    "TEX": {"mlb_id": 140, "name": "Texas Rangers", "league": "AL", "division": "AL West", "color": "#003278",
            "city": "Texas", "ballpark": "Globe Life Field · Arlington, TX"},
    "TOR": {"mlb_id": 141, "name": "Toronto Blue Jays", "league": "AL", "division": "AL East", "color": "#134A8E",
            "city": "Toronto", "ballpark": "Rogers Centre · Toronto, ON"},
    "WSN": {"mlb_id": 120, "name": "Washington Nationals", "league": "NL", "division": "NL East", "color": "#AB0003",
            "city": "Washington", "ballpark": "Nationals Park · Washington, DC"},
}

BREF_ALIASES = {"ATH": "OAK"}

MLB_ID_TO_TEAM = {meta["mlb_id"]: code for code, meta in TEAMS.items()}


def canonical_team(code: str) -> str:
    return BREF_ALIASES.get(code, code)


def logo_url(team: str) -> str:
    return LOGO_URL.format(mlb_id=TEAMS[team]["mlb_id"])


def primary_logo_url(team: str) -> str:
    return PRIMARY_LOGO_URL.format(mlb_id=TEAMS[team]["mlb_id"])
