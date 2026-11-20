# M1 — Three home-page directions

**Site name:** Full Count (chosen 2026-11-20)
**Date:** 2026-11-20

All three build the **same page with the same words**, so the comparison is about the design and
not about which one got more effort:

- wordmark, h1, lede, and a "What drives the number" box
- the line *Every section is a pitch*
- a batter at the plate in front of the strike zone, six numbered pitches in and around it
- six tiles — Predictions, Players, Teams, Model, Matchups, About the data
- one footer line naming the data sources

**Picking a direction picks a token system**, not just a look: each file's `:root` is a complete
set of color, type and spacing values that the whole app would then use.

Shared behavior in all three: hovering or keyboard-focusing a tile lights its pitch in the strike
zone, and the reverse. That cross-highlight is pure CSS (`:has()`), no JavaScript.

---

## Direction A — Scorebook

**Concept.** A statistician's notebook. The six tiles are the ruled cells of a scorecard,
separated by hairlines; the strike zone is a hand-ruled 3×3 grid; the pitch marks are baseballs
with red-pencil seams.

| Token | Value |
|---|---|
| `--ground` | `#16130f` — warm near-black, browner than the NFL site's `#14110f` |
| `--panel` | `#1e1a15` |
| `--rule` | `#352d24` |
| `--text` | `#f1e8da` |
| `--muted` | `#a99b87` |
| `--chalk` | `#e6dac3` |
| `--accent` | `#dd6348` — red pencil |

**Type.** Barlow Condensed 600/700 for display, Barlow 400/500/600 for body. One family, two
widths — and Barlow Condensed is already loaded by the current app, so this direction commits to
a face the project half-owns rather than adding a new one.

**Strengths.** The densest and most "statistics" of the three; the hairline cell grid is a real
idea rather than a style, and it extends naturally to the data screens, where tables and
leaderboards already want ruled cells. Condensed display gives large headlines in little space.

**Weaknesses.** Closest of the three to the NFL site's warm-dark family — a sibling, but the most
likely to read as a repeat. Condensed type is less comfortable at small sizes than the other two.
The accent had to be lightened from `#d2543a` to `#dd6348` to clear 4.5:1 on panels, which made
it slightly less "pencil".

---

## Direction B — Broadcast

**Concept.** The pitch-tracker overlay. Cool ground, dashed zone grid, accent corner ticks,
tracked pitch trails with velocity readouts. The tiles are instrument panels with a top rule that
lights on hover.

| Token | Value |
|---|---|
| `--ground` | `#0b1016` |
| `--panel` | `#131c25` |
| `--panel-2` | `#192530` |
| `--rule` | `#26323f` |
| `--text` | `#e9f1f8` |
| `--muted` | `#93a7b9` |
| `--chalk` | `#cadced` |
| `--accent` | `#c3f53c` — tracker chartreuse |

**Type.** Space Grotesk 500/700 display, Inter 400/500/600 body.

**Strengths.** The most technical and the most distinct from the NFL site — nobody would call it a
reskin. The brightest accent by far (14.95:1 on the ground), so calls to action and live values
carry. Of the three it suits charts best: a cool ground makes data colors sit calmly.

**Weaknesses.** **It deliberately breaks the family trait** — the agent definition says warm, and
this is cool. It is the direction that tests whether warmth is actually required. The velocity
readouts are invented numbers; they would have to become real values or be dropped. Chartreuse is
a strong flavor and dates faster than the other two.

---

## Direction C — Field Chalk

**Concept.** A diagram, not a dashboard. No panels anywhere — type sits directly on the ground,
separated by air and hairlines. The strike zone is a single thin rectangle with no inner grid, and
leader lines run from each pitch out toward its tile.

| Token | Value |
|---|---|
| `--ground` | `#1b1714` |
| `--panel` | `#241f1a` (barely used) |
| `--rule` | `#3a3129` |
| `--text` | `#f4ece1` |
| `--muted` | `#b0a292` |
| `--chalk` | `#ded2c0` |
| `--accent` | `#8fbfa8` — faded outfield chalk |

**Type.** Fraunces 400/600 display (variable optical size), Work Sans 400/500 body.

**Strengths.** The most designed and the quietest; the serif gives the site an editorial voice the
other two don't have, and the restraint ages well. Highest accent contrast of the warm pair
(8.64:1). The no-panel approach is the cheapest to maintain — fewer surfaces to keep consistent.

**Weaknesses.** The quiet is a risk for a portfolio piece: it asks the viewer to lean in, where the
brief is "memorable in a few seconds". Fraunces is a distinctive face and will fight the team
logos. Without panels, the data screens have less structure to inherit — the restyle of Players
and Teams would need more invention than in A or B.

---

## Checks run on all three

- **Contrast**, computed per token pair against WCAG 2.2 AA (4.5:1 body, 3:1 large text and UI):
  all text, muted, chalk and accent values pass on both ground and panel in all three directions
  after A's accent was lightened. Numbers are in the round report.
- **Hairline rules** sit at 1.3–1.5:1 in all three. These are decorative separators, exempt from
  SC 1.4.11; the tiles are identified by their text, not by their border, and every focus
  indicator passes 3:1 (A 5.25, B 14.95, C 8.64). Say the word and the rules get lightened.
- **Keyboard:** every tile is an `<a>` with a visible `:focus-visible` indicator; the cross-
  highlight fires on focus as well as hover.
- **Reduced motion:** all transitions disabled under `prefers-reduced-motion: reduce`.
- **Layout** shot at 1440 and at 390. All three stack cleanly on a phone: the diagram sits above
  a single column of tiles, nothing overflows, no sideways scroll. Page heights at 390 are
  A 1793px, B 1863px, C 1785px — about three phone screens each.
- **Number alignment.** The checker caught the pitch-kind labels in C sitting 21px off a common
  edge, because Fraunces sets proportional figures and "1" is narrower than "3". Fixed with
  `font-variant-numeric: tabular-nums`, applied to all three for the same reason.

### Known, expected findings

- Every tile links to `#`. These are direction mockups; the destinations do not exist yet.
- C's leader lines run off to the right on a phone, where there is no list beside them to point
  at. They should be hidden below 820px in the refinement round if C is chosen.
- The kit's checker reports `hero-screen`, `section-height`, `one-section`, `container-edges`,
  `row-lines`, `card-visual` and `cta` on all three (and `section-air` on C at 390). Those rules are written for a marketing
  page built as `header.nav` + full-screen sections + `footer.closing`, with a photograph or an
  icon in every card and a button in the hero. This is a one-screen app home page with a diagram,
  so they do not apply. Equal edges were verified in the screenshots instead — and in C's case by
  the checker itself, which measured 174px left and 174px right and failed it only for exceeding
  the kit's 64–120px margin preference.
