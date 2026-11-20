# Round 1 — M2: the home page, Direction A refined

**File:** `home.html` · **Date:** 2026-11-20 · **Status:** awaiting review

Direction A (Scorebook) taken from `directions/direction-a.html` and refined to a final home page.

## What changed since the direction

**The strike zone was wrong.** It ran from the letters down past the batter's knees to his shins.
A strike zone stops at the hollow of the knee. The zone is now `y 152–266` against a batter whose
knees are at ~264 — letters to knees, as it should be. All six pitches were repositioned to match:

| # | Pitch | Where it sits now |
|---|---|---|
| 1 | Four-seam fastball | Dead centre of the zone |
| 2 | Slider | Low away, on the corner, half outside the edge |
| 3 | Curveball | Upper third, inside the zone |
| 4 | Changeup | In the dirt, below the zone |
| 5 | Sinker | Low inside, in the zone |
| 6 | Cutter | Off the plate, up and in — a clear ball |

**Home plate** was floating below its own ground line. It now lies on the same ground plane as the
batter, centred under the zone.

**The batter's box is actually drawn** — a chalk outline in perspective under the batter's feet.
The page is called Batter's Box; it should show one. It replaces the stray horizontal ground line.

**The diagram fills its column.** The old viewBox left ~64px of dead space on the right; it is now
cropped to the drawing's real bounds, so the figure is larger at the same column width.

**Real destinations.** The six tiles now point at `#predictions`, `#players`, `#teams`, `#model`,
`#matchups`, `#about` instead of `#`.

**Tabular figures** on the pitch numbers, so the kind labels line up across cells.

**Single column from 640px** (was 560px), so 375 never tries to squeeze two tiles.

## Defects found and fixed in this round

1. **Focus state had a contrast hole.** Focusing a tile by keyboard filled its pitch dot with the
   accent, but the number inside it only darkened on `:hover` — so a keyboard user saw chalk on
   red at **2.55:1**. The `:focus-visible` case was missing from that rule. Fixed: **5.39:1**.
2. **The focus ring was a `box-shadow` only**, which Windows forced-colors mode discards, leaving
   no visible ring. Added a transparent `outline` so a ring survives there. No visual change
   anywhere else.

## Checks

**Contrast** (WCAG 2.2 AA — 4.5:1 body, 3:1 large text and UI):

| Pair | Ratio | Needs | |
|---|---|---|---|
| text `#f1e8da` on ground | 15.25 | 4.5 | PASS |
| text on panel `#1e1a15` | 14.25 | 4.5 | PASS |
| muted `#a99b87` on ground | 6.81 | 4.5 | PASS |
| muted on panel | 6.36 | 4.5 | PASS |
| accent `#dd6348` on ground | 5.25 | 4.5 | PASS |
| accent on panel | 4.90 | 4.5 | PASS |
| chalk `#e6dac3` on ground | 13.39 | 4.5 | PASS |
| pitch number on a lit dot | 5.39 | 4.5 | PASS (was 2.55) |
| focus ring `#dd6348` on ground | 5.25 | 3.0 | PASS |

Hairline rules sit at 1.37:1. They are decorative separators (SC 1.4.11 exempts them); the tiles
are identified by their text and their focus ring, not by their border. Open question 6 still
stands — say the word and they get lightened.

**Keyboard.** Six focusable elements, tab order 1→6 in reading order, no traps, no off-screen
focus. The focus ring is a 2px inset accent ring, confirmed visible in a screenshot. The
cross-highlight fires on focus as well as hover.

**Edges.** Measured rather than eyeballed, at 1280: `.mark`, `.head-row`, `.today`, `.cue`,
`.box`, `.pitches` and the footer all run **90px from the left and 90px from the right**.

**Layout.** Shot at 1280 (916px tall), 768 (1410px) and 375 (1795px). Single column from 640px
down; nothing overflows and there is no sideways scroll at any width.

**Performance** (`perf.mjs`): **0 FAIL**. First and largest contentful paint 64ms, cumulative
layout shift 0.000, 130 DOM nodes, no WebGL contexts, no broken requests.

**Reduced motion.** All transitions disabled under `prefers-reduced-motion: reduce`.

## Known and expected

- The six links point at section ids that do not exist yet — this page is still standalone. They
  resolve when the home page is merged into `index.html` at M6.
- The kit's checker reports `hero-screen`, `section-height`, `one-section`, `card-visual` and
  `cta`: rules for a marketing page built of full-screen sections with a photo in every card and
  a button in the hero. Not applicable to a one-screen app home page built around a diagram.
- It also reports `container-edges` and `row-lines`. Both are false positives, confirmed by the
  measurements above: the checker was reading the h1 and lede, whose widths are capped on purpose
  for line length.
