# Round 3 — M4: Players and Teams, restyled

**Files:** `players.html`, `teams.html`, `tokens-draft.css` · **Date:** 2026-11-20 · **Status:** awaiting review

Numbers shown are illustrative, not live data.

## The headline: M4 needed no JS rewrite

I flagged this as the riskiest milestone three times, on the assumption that the hand-written
chart code had colour literals baked in. **It does not.** `drawRanked` and `drawScatter` already
draw with CSS variables and classes:

```
fill="var(--accent)"  stroke="var(--bg)"  fill="var(--muted-dot)"
class="gridline" | "refline" | "stem" | "stripe" | "dim" | "hit"
```

The only colour literal in the whole JS half is `#888`, a fallback for a missing team colour —
and that is data, not styling.

So the restyle is a token swap. The old names (`--bg`, `--border`, `--grid`, `--text-dim`,
`--muted-dot`, `--radius`) are **aliased to the new values** at the bottom of `:root`, and every
existing rule and every SVG the JS emits picks up the Scorebook palette untouched. That alias
block is in `tokens-draft.css` and is the thing M6 actually has to paste.

This makes M4 the safest milestone, not the riskiest. My earlier warning was wrong.

## One real exception, and it does need a JS edit

`drawScatter` sets `fill-opacity="${hl ? 0.95 : 0.55}"`. The non-highlighted dots — which are most
of a scatter — composite down to **1.66:1** against the panel at that opacity. A scatter's dots
are graphical objects needed to understand the content, so they fall under SC 1.4.11 and want
3:1. A token change alone cannot fix it, because the opacity lives in the JS.

| Option | Result | Cost |
|---|---|---|
| A. Lighten the token, keep opacity `0.55` — `--muted-dot: #b3a28a` | **3.03:1**, barely over | No JS change, but the muted dots end up as bright as body text and the highlighted dot stops standing out |
| **B. `--muted-dot: #8f7d66` and opacity `0.55 → 0.85`** | **3.51:1** | One numeric literal in `drawScatter` |

**I took B**, on the grounds that a `fill-opacity` value is styling, so changing it sits inside
"restyle, don't rebuild". It is flagged in the token file and is the one line M6 must change in
the JS. Say the word and I will switch to A instead.

## What changed

- **Controls** become square: hairline-bordered selects and number inputs on the page ground,
  segmented buttons as a single ruled strip with the active segment on `--panel-2`.
- **Labels** are condensed uppercase with letter-spacing, matching Predictions.
- **The tiles grid** on the Teams detail becomes a ruled grid — 1px gaps over `--rule`, so it
  reads as scorecard cells rather than floating boxes.
- **Chart surfaces** inherit everything: stripes on `--panel-2` at 0.55, gridlines and stems on
  `--rule`, values in `--muted`, markers in `--accent`.
- Stat values and chart tick labels use **tabular figures**.

## Defects found and fixed in this round

1. **The Stat select ballooned.** With only three controls in the Teams row, `flex: 1 1 170px`
   stretched the select to ~730px. Capped at `max-width: 280px`.
2. **The tiles grid showed an empty cell.** `repeat(auto-fill, …)` creates a seventh track for six
   tiles; harmless with the old 10px gaps, but obvious once the grid is 1px rules over a
   background. Changed to `auto-fit`.
3. **The charts were illegible at 375 — in the mockup only.** A static SVG with a 1064-wide
   viewBox scales down to ~35% on a phone, shrinking 12px text to roughly 4px. The live app never
   does this: the JS re-renders at `clientWidth`, and under 520px it switches to a narrow layout
   with 118px labels, names truncated to 14 characters and 4 ticks instead of 6. Rather than
   explain that away, both variants are now embedded and swapped at the same 520px threshold the
   JS uses, so the mockup shows what the app genuinely renders at each width.

## Checks

| Pair | Ratio | Needs | |
|---|---|---|---|
| chart text on panel | 14.25 | 4.5 | PASS |
| chart `.dim` labels on panel | 6.36 | 4.5 | PASS |
| accent marker on panel (at 0.95) | 4.53 | 3.0 | PASS |
| muted scatter dot, option B | 3.51 | 3.0 | PASS |
| muted scatter dot, as inherited | 1.66 | 3.0 | **FAIL — fixed by option B** |
| nav, labels, section notes | as round 2 | | PASS |

Gridlines, stems and row stripes sit below 3:1 by design — they are decorative scaffolding, not
content, and every value they support is also printed as text beside its marker.

**Layout.** Players 1280 (924px) and 375 (1503px); Teams 1280 (1400px) and 375 (2551px). Two-column
detail stacks at 820. Charts swap to the narrow variant at 520.

**Reduced motion.** Transitions disabled under `prefers-reduced-motion: reduce`.

## Known and expected

- Team crests are lettered circles, ~18px in the chart rows. The live app puts a real 16px MLB
  logo there, which will read better than two or three letters at that size.
- The **Compare** (scatter) view is not mocked — only the leaderboard and rankings views are. The
  scatter shares every token and class shown here; what it does not share is the dot-opacity
  question above, which is why that is called out rather than drawn.
- Nav links point at section ids that do not exist until M6.
