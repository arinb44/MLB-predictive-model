# Round 4 — M5: Model, Matchups, About the data

**Files:** `model.html`, `matchups.html`, `about.html` · **Date:** 2026-11-20 · **Status:** awaiting review

The three new pitches. Built from `build.py` + `content.py` so all three share one style block
lifted from round 3 — no third copy of the design system.

## Matchups needs a backend route, and that is out of scope

This is the one thing to decide before M6.

Head-to-head history means *results of games between two specific teams*. The API has no route
that returns them. Existing routes are `/predict`, `/teams`, `/roster/{team}`, `/teams/meta`,
`/stats/players`, `/stats/teams` — none carries a game log.

The **data exists** in the project: `fetch_season_game_log` and `to_team_game_long` in
`src/data/fetch.py` build exactly this, and it is what the model trains on. What is missing is an
endpoint, something like `GET /head-to-head/{team_a}/{team_b}` returning date, home, away and the
final score per meeting.

The approved plan puts new backend routes **out of scope** ("No new backend routes or a
`StaticFiles` mount, unless separately approved"). So this page is designed and ready, and
shipping it needs your approval for one new read-only route. Without that, the honest options are
to ship five pitches or to leave Matchups as a stub.

## The Model page uses the README's numbers, not invented ones

Everything on it comes from `README.md`: the feature groups, the three models, and the
walk-forward table (2015–2024, 22,614 games, trained models tested on 2018–2024 after a
three-season burn-in). The 55–58% ceiling argument and the leakage note are the README's own
framing, including that `tests/test_features.py` enforces it rather than the README claiming it.

**One discrepancy you should settle.** The live UI's subtitle says *"Only team form, Elo, and the
trailing starter proxy drive the prediction"*. The README describes a wider feature set — rest
days, bullpen fatigue, park factors and starting-pitcher identity as well — and
`get_feature_columns` takes everything in `features.csv` minus a non-feature list, which matches
the README. The Model page follows the README. If the UI subtitle is the accurate one, the Model
page needs trimming; if the README is, the subtitle on Predictions is understating the model.
I have not changed either.

## Defects found and fixed in this round

1. **Orphan grid cells, again.** `repeat(auto-fit, minmax(240px, 1fr))` gave four tracks for six
   cells, leaving two empty cells showing the grid's rule colour — the same class of bug fixed in
   round 3, reintroduced in a different grid. Column counts are now explicit: `.cells` is 2 up,
   `.cells.three` is 3, stepping to 2 at 900px and 1 at 560px. No arrangement leaves an orphan.
2. **The Matchups scores did not reconcile.** With scores written away-first and no fixture
   label, four of the seven games were ambiguous and the Jun 16 row contradicted its own winner
   chip. Each row now names the fixture (`BOS at LAD` / `LAD at BOS`) so the score order is
   unambiguous. The arithmetic is now verified rather than asserted: the seven games give Boston
   3 wins of 7 — matching the 3–4 series — and a run differential of **+4**, where the page had
   said −6. Corrected.
3. **The sources table read badly at 375.** Right-aligned cells whose text wraps to three lines
   look broken; all cells go left-aligned below 560px.

## Checks

| Pair | Ratio | Needs | |
|---|---|---|---|
| cell tag accent on panel | 4.90 | 4.5 | PASS |
| table body text on striped row | 13.33 | 4.5 | PASS |
| table head muted on panel | 6.36 | 4.5 | PASS |
| inline code chalk on panel | 12.51 | 4.5 | PASS |
| winner chip, left picker, on striped row | 4.59 | 4.5 | PASS |
| winner chip, right picker, on striped row | 6.85 | 4.5 | PASS |
| highlighted result cell on striped row | 4.59 | 4.5 | PASS |

The winner chip's colour means *which of the two pickers*, not home or away — the fixture column
carries home and away now, so the colour is not doing double duty.

**Layout.** Model 1280 (1606px) / 375 (2889px); Matchups 1280 (1008px) / 375 (1823px); About 1280
(1198px) / 375 (1901px). Cell grids step 3 → 2 → 1; the head-to-head block stacks at 820; game
rows drop to three columns at 820.

**Reduced motion.** Transitions disabled under `prefers-reduced-motion: reduce`.

## Known and expected

- Nav links still point at ids that do not exist until M6.
- The Model page does not yet surface `reports/shap_gbm_summary.png` or
  `reports/shap_baseline_summary.png`. Those are real artefacts worth showing, but they are PNGs
  in `reports/`, and with no static mount there is no URL that serves them. That is the same
  question as open question 4 and should be settled with it.
- Matchups shows one season's meetings. Multi-season history is a bigger ask and would widen the
  route above.

---

## Update, 2026-11-20 — logos restored and the route approved

**Real MLB logos are back across every mockup**, loaded the way the live app loads them via
`logo_url` / `primary_logo_url` in `src/data/teams.py`:

- `team-cap-on-dark/{id}.svg` for the side and stat-panel crests on Predictions, the team banner
  on Teams, the picker heads and every game row on Matchups, and the row labels in both charts.
- `team-primary-on-dark/{id}.svg` **masked into the matchup card**, which restores the part of
  that component's design I had dropped — the logo fading in from each edge under a team-colour
  glow. The team name sits over it by design, so it gained a text shadow to stay legible.
- The Teams rankings chart now uses **cap logos as the markers themselves**, 26px, exactly as
  `marker: "logo"` does in the live app — not accent dots.

Team codes in the mockups were corrected to the project's own Baseball-Reference style (`KCR`,
`SDP`, not `KC`, `SD`).

**Two real defects the logos introduced, both fixed.** `perf.mjs` flagged six images with no
`width`/`height` (a layout-shift source) and two below-fold images not lazy-loaded. All logo
images now carry intrinsic dimensions and `loading="lazy"`. Predictions, Teams and Matchups are
now **0 FAIL** on `perf.mjs`, with zero broken requests — the remote logos do load.

The remaining `upscaled image` warning (`119.svg` natural 145px shown at 196px) is a false
positive: these are SVGs, which have no fixed resolution to upscale from.

**One correction to the page's own copy.** The pickers said Boston was away in 4 of 7 meetings and
Los Angeles home in 4 of 7. Three of the seven are at Dodger Stadium and four at Fenway, so both
are **3 of 7**. Fixed.

**The head-to-head route is approved.** Its contract is in `head-to-head-endpoint.md` — path,
parameters, response shape, error cases, and the constraint that it stays display-only and never
reaches the feature pipeline. It is written now so the page and the endpoint agree, and lands in
`src/api/main.py` during M6 rather than now, because a route with no consumer is dead code.
