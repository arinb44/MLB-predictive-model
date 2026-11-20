# Head-to-head endpoint — contract

**Approved by the user on 2026-11-20.** Written now so the page and the route agree; it lands in
`src/api/main.py` during M6, alongside the merge, because a route with no consumer is dead code.

## Why one is needed

The Matchups page shows results of games between two specific teams. No existing route returns
them — `/predict`, `/teams`, `/roster/{team}`, `/teams/meta`, `/stats/players` and `/stats/teams`
carry no game log. The data is already in the project: `fetch_season_game_log` and
`to_team_game_long` in `src/data/fetch.py` build exactly this, and it is what the model trains on.

## Shape

```
GET /head-to-head/{team_a}/{team_b}?season=<int>
```

- `team_a`, `team_b` — the project's own team codes (Baseball-Reference style: `BOS`, `LAD`,
  `KCR`, `SDP`). Run both through `canonical_team()` so aliases resolve.
- `season` — optional, defaults to the current season. The page shows one season; see Limits.

### Response

```jsonc
{
  "team_a": "BOS",
  "team_b": "LAD",
  "season": 2025,
  "a_wins": 3,
  "b_wins": 4,
  "a_run_diff": 4,          // team_a runs minus team_b runs, across every meeting
  "last_meeting": "2025-08-02",
  "games": [                 // most recent first
    {
      "date": "2025-08-02",
      "home": "LAD",         // a code, so the page can label "BOS at LAD"
      "away": "BOS",
      "home_runs": 5,
      "away_runs": 2,
      "winner": "LAD"
    }
  ]
}
```

The page derives everything else from this: the series line, the run differential, how many
meetings each side hosted, and the per-row fixture label.

### Errors

- `404` if either code is unknown after `canonical_team()`.
- `400` if `team_a == team_b`, matching how `/predict` already rejects a team against itself.
- An empty `games` list is a valid 200 — two teams can simply not have met yet.

## Constraints

- **Read-only.** No writes, no model call, no new dependency.
- **Not a model input.** Head-to-head results must not reach the feature pipeline. Seven games is
  far too small a sample, and the page says so in as many words. This endpoint is display only,
  like `/stats/players` and `/stats/teams`.
- **No leakage risk**, since nothing here is consumed during training or prediction.

## Limits

- One season per call. Multi-season history would mean either a `seasons` range parameter or
  dropping the filter, and would change the page's shape; not designed.
- Depends on game-log coverage for the requested season being present in the processed data.
