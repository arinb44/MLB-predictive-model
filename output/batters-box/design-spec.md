# Full Count: Design Specification

**Prepared by:** Strike Zone (`output/batters-box/designAgent.md`)
**Date:** 2026-11-20
**Updated:** 2026-11-24, M7: a realistic swing and spinning balls (§10)
**Status:** Final

## 1. Overview

The MLB Game Outcome Predictor is now **Full Count**. A new home page puts a batter at the plate
in front of a strike zone, with six pitches placed in and around it — each pitch a section of the
site. The three existing screens kept their layouts and logic and took on a new palette, type and
panel style; three new sections were added. It reads as a sibling of
[Fourth and Why](https://arinb44.github.io/NFLGamePredictorModel/) — same structural grammar,
its own warm palette and baseball motifs, none of its hex values.

Direction **A, "Scorebook"** was chosen from three: a statistician's notebook, where tiles are the
ruled cells of a scorecard and the strike zone is a hand-drawn grid.

## 2. Design Rationale

Three directions were built as complete token systems: **A Scorebook** (warm, dense, ruled),
**B Broadcast** (cool, technical, chartreuse — deliberately breaking the warm family trait to test
it), and **C Field Chalk** (warm, quiet, serif, no panels). A won on one argument: its core idea,
the ruled cell, survives contact with the boring screens. Leaderboards and team tables already
want ruled cells, so the home page's conceit and the data views share one grammar. B was the most
striking in isolation and the weakest bet for Players and Teams; C was the prettiest and the
quietest, and quiet works against a portfolio-first brief.

## 3. Visual Foundations

### Colour

| Token | Hex | Use | Contrast on ground / panel |
|---|---|---|---|
| `--ground` | `#16130f` | Page | — |
| `--panel` | `#1e1a15` | Cards, panels | — |
| `--panel-2` | `#252017` | Inset surfaces, tiles, chart stripes | — |
| `--rule` | `#352d24` | Hairlines | 1.37 (decorative) |
| `--text` | `#f1e8da` | Body | 15.25 / 14.25 |
| `--muted` | `#a99b87` | Labels, captions | 6.81 / 6.36 |
| `--chalk` | `#e6dac3` | Diagram lines, balls, the batter's gloves; his other parts mix it into the ground (§10) | 13.39 / 12.51 |
| `--accent` | `#dd6348` | Red pencil: the one accent | 5.25 / 4.90 |
| `--accent-ink` | `#1a0d08` | Text on an accent fill | 5.39 on accent |
| `--away` | `#dd6348` | Away side | 5.25 / 4.90 |
| `--home` | `#79b0cc` | Home side | 7.84 / 7.33 |
| `--muted-dot` | `#8f7d66` | Unhighlighted scatter dots | 3.51 at 0.85 opacity |

Red against blue for home/away stays separable under deuteranopia and protanopia, which
red/orange does not.

### Typography

- **Display:** Barlow Condensed 500/600/700 (800/900 retained for the matchup card). Headings,
  labels, numbers, buttons, nav.
- **Body:** Barlow 400/500/600.
- Both from Google Fonts, free for web use. Barlow Condensed was already loaded by the old page
  but barely used; this direction commits to it.
- Numbers use `font-variant-numeric: tabular-nums` wherever they form a column.

### Spacing and layout

`--s1 4px`, `--s2 8px`, `--s3 12px`, `--s4 18px`, `--s5 28px`, `--s6 44px`. One container
(`.wrap`, max 1180px, 40px padding → 24px on phones). Radius is **0 everywhere**.

### Iconography and imagery

No illustration beyond the batter's-box diagram. Team logos are MLB's own, loaded at display time
from `team-cap-on-dark/{id}.svg` and `team-primary-on-dark/{id}.svg` via `src/data/teams.py`.

## 4. Screens

Seven views, all in `src/api/static/index.html`, switched by `showTab()` with no routing.

| View | id | Notes |
|---|---|---|
| Home | `tab-home` | Batter's box; each of the six pitch tiles (pitch type, section, one line; no numbers) throws its pitch at the batter, who swings (§10), then opens its section after a one-second hold. Balls are hidden until thrown |
| Predictions | `tab-predict` | Unchanged layout, controls and `/predict` payload; matchup card keeps its own design, corners squared |
| Players | `tab-players` | Unchanged chart logic; restyled by token alias alone |
| Teams | `tab-teams` | As above, plus ruled tile grid |
| Model | `tab-model` | New. Features, the three models, the walk-forward table, the ceiling argument |
| Matchups | `tab-matchups` | New. Season series and every meeting, from `GET /head-to-head/{a}/{b}` |
| About the data | `tab-about` | New. Sources, model inputs vs context, caveats |

States covered: hover (tiles lift 2px), focus (2px inset accent ring plus a
transparent outline so forced-colors keeps a ring), loading (the existing calibrating bar;
Matchups shows "Loading…"), empty (Matchups when two teams have not met), error (Matchups when the
fetch fails).

## 5. Components & Tokens

Tokens live in the `:root` of `src/api/static/index.html`; the source-of-truth copy is
`output/batters-box/final/tokens.css`. The second half of that block **aliases** the names the
existing CSS and chart JS already use — `--bg`, `--border`, `--grid`, `--text-dim`, `--muted-dot`,
`--radius` — which is why the hand-written SVG chart code needed no rewrite.

The batter's-box diagram is inline SVG (no static mount exists to serve a file); a standalone copy
is `output/batters-box/final/batters-box.svg`, exported from the page as it draws on load by
`iterations/round-6/export-svg.js`.

## 6. Accessibility & Responsiveness

- **WCAG 2.2 AA.** Every text, label, accent and marker pair was measured; all pass. Ratios in §3.
- Hairline rules sit at 1.37:1 as decorative separators (exempt under SC 1.4.11); controls are
  identified by text and focus ring, not border.
- **Keyboard:** every view reachable, tab order follows reading order, visible focus everywhere.
- **Breakpoints:** 1280 / 1024 / 820 / 640 / 560 / 390. No horizontal overflow at 390 (measured:
  `scrollWidth === clientWidth === 390`).
- **Reduced motion:** all transitions disabled under `prefers-reduced-motion: reduce`; no pitch is
  thrown and the batter doesn't swing, so a tile opens its section at once.
- **Colour independence:** the probability bar prints its percentages inside both segments.

## 7. Files & Links

**Project source tree (changed):**
- `src/api/static/index.html` — tokens, seven views, restyle, tab wiring, scatter opacity, prob-bar labels;
  at M7 the swing rig and the spinning balls
- `src/api/main.py` — `GET /head-to-head/{team_a}/{team_b}`
- `tests/test_api.py` — title assertion updated; two tests added for the new route

**Design project (`output/batters-box/`):** `designAgent.md`, `plan.md`, `progress.md`,
`decisions.md`, `design-spec.md`, `directions/` (3 directions, 3 swing directions + README),
`iterations/round-1…6` (each with NOTES.md; round 5 holds the rig, its self-check and `build.py`,
round 6 the balls and the SVG export), `final/tokens.css`, `final/batters-box.svg`, `shots/`.

No Figma files.

## 8. Decision Log

Thirty-three decisions in `decisions.md`. The ones that shaped the result: sibling-not-clone identity;
home page plus restyle (not a full rebuild); six pitches; the name **Full Count**; Direction A;
red/blue for home and away; keeping the matchup card and squaring only its corners; aliasing
tokens rather than renaming; `fill-opacity` 0.85 for scatter dots; Matchups as head-to-head
history; approving one new read-only route; real MLB logos. At M7: a rig at true proportions in slow
motion (×2.1) rather than real time; direction C, Uniform; the new still pose; spinning balls with no
numbers or dotted outline, and no numbers on the tiles either.

## 9. Known Issues & Next Steps

- **The Predictions subtitle may be wrong.** It says only team form, Elo and the starter proxy
  drive the number; the README and `get_feature_columns` describe a wider set (rest, bullpen
  fatigue, park factors, pitcher identity). The Model page follows the README. One of the two
  needs correcting — not a design call.
- **SHAP charts are not surfaced.** `reports/shap_gbm_summary.png` and `shap_baseline_summary.png`
  would suit the Model page, but there is no static mount to serve them.
- **The "Calibrating…" bar and the error state** were not individually restyled; they inherit the
  tokens but were not designed as states.
- **Matchups covers one season** (the latest in `game_log.csv`, currently 2024). Multi-season
  history would widen the route.
- **The Compare (scatter) view** was never mocked; it inherits the tokens and the dot-opacity fix.
- **Seams sit at 2.55:1 against the ball.** Decoration on an `aria-hidden` element; passing would
  mean leaving `--accent`.

## 10. The swing (M7, 2026-11-24)

The five-layer CSS swing was replaced by a small vanilla-JS rig, `BatterRig` in `index.html` (source:
`iterations/round-5/swing-rig.js`), in direction **C, Uniform**.

- **Model.** A 3D skeleton at real proportions (thigh and shin 0.45 m, upper arm 0.29, forearm
  0.32, a 34-inch bat with the sweet spot 0.70 m from the knob), projected in perspective from the
  umpire's eye, 1.35 m up and 6 m back. Two-bone IK places knees and elbows; both hands stay on the
  bat. The torso is the hull of stacked elliptical rings, so it turns instead of sliding. Body,
  arms and bat are depth-sorted every frame.
- **Swing.** Eight keyframes in real seconds, contact at 0: stance −0.43, load −0.27 (hands back,
  front foot up), plant −0.16 (stride down), slot −0.075 (barrel drops behind the hands),
  contact 0 (front leg braced, hips leading the shoulders, barrel through the zone), extension
  0.05, rollover 0.12, finish 0.26 (bat over the front shoulder). Monotone cubic interpolation per channel, so nothing
  overshoots.
- **Timing.** Slowed ×2.1 at true proportions: a 430 ms swing takes 900 ms, so contact lands when
  the fastball does, 900 ms after release. The same swing runs on every pitch; on the five that
  miss it starts early and the barrel is through the zone about 170 ms before the ball, which is how
  a hitter misses off-speed. He holds the finish until the section opens; `showTab()` puts him back
  in his stance.
- **Look.** Each part is one solid tone of `--chalk` mixed into `--ground` with `color-mix()`, so
  no new tokens: shoes 40%, helmet 46%, socks 48%, pants 56%, jersey 72%, arms 82%; gloves and
  handle in chalk, barrel in accent, a ground-coloured belt. Solid tones let overlapping parts cover
  each other instead of brightening. A short accent ribbon trails the barrel from the slot to the
  rollover only.
- **Contrast** on `--ground`: gloves 13.39, arms 9.25, jersey 7.36, barrel 5.25, pants 4.90, socks
  3.92, helmet 3.70, shoes 3.10. Every part clears 3:1 (SC 1.4.11).
- **Balls.** Solid chalk (13.39:1) with no number and no dotted outline. The seam is the real curve
  on a sphere, turned each frame about the pitch's own spin axis and drawn where it faces us:
  backspin on the four-seam, gyro on the slider and cutter, topspin on the curve, arm-side tilt on
  the changeup, sidespin on the sinker. Relative rates are real (1,750–2,500 rpm), slowed so a 2,300 rpm pitch
  turns 2.2 times on its way in.
- **Self-check.** `iterations/round-5/check-rig.js` samples the swing every 2 ms: hands on the bat,
  legs reach their feet, every point inside the viewBox, contact inside the zone, the swing clock
  never runs backwards, the fastball is met at 900 ms and misses are early. `build.py` runs it
  before it writes.
- **Verified** against the running API: the swing runs; the fastball is met at (277.7, 216.5) with
  the burst; "Strike" shows on a miss; the section opens and the stance returns; no console errors;
  25/25 tests pass. Also checked at 1280, 768 and 375 and with reduced motion.

