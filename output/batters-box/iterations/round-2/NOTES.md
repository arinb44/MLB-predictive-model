# Round 2 — M3: Predictions, restyled

**File:** `predictions.html` · **Date:** 2026-11-20 · **Status:** awaiting review

The Predictions screen in Direction A's tokens. Layout, controls, field order and the `/predict`
request shape are unchanged — team select, starting pitcher, up to three hitters per side, date,
Predict, then card / bar / two stat panels. Only surface styling moves.

The numbers shown (BOS @ LAD, 41.7 / 58.3) are **illustrative**, not model output.

## Two decisions this round forced

### 1. Home and away need two colours

The old palette used `--home #4f8cff` and `--away #ff8a4f` — a blue and an orange that belong to
the slate theme and clash with a warm ground. Direction A has one accent, but the probability bar,
the side panels and (at M4) the charts genuinely need two separable colours.

**Chosen:** `--away #dd6348` (the Scorebook accent red) and `--home #79b0cc` (a chalk blue).

Red against blue stays separable under deuteranopia and protanopia, which red/orange and
red/green do not. Both clear 3:1 on every surface: away 5.25:1 on ground and 4.90:1 on panel,
home 7.84:1 and 7.33:1.

The probability bar also **prints its percentages inside the segments**, so the split is readable
with no colour perception at all — the old bar was a bare 10px stripe that said nothing on its
own.

### 2. The matchup card is existing deliberate design

`.mc` is not generic styling. It is a designed component — team-colour glow, film grain, logos
masked to fade in from each edge, a count-up on the percentages — carried over from a Figma Make
template, with a build guide in `docs/`. It is the one part of the current app with real visual
intent.

**Chosen: keep it, change one property.** Its `border-radius` goes from `16px` to `0` so it sits
in a system with square corners everywhere else. Everything else about it is untouched.

The argument for keeping it: the card is a *broadcast graphic embedded in a page*, and reads as a
deliberate change of register rather than an inconsistency — the way a TV score bug looks nothing
like the page around it. The argument against: it is the only rounded, glowing, team-coloured
object in an otherwise flat, warm, hairline-ruled site.

**This is yours to overrule.** If you want the card rebuilt in Scorebook tokens, that is a round of
its own, and the `docs/` build guide would need updating with it.

## What else changed

- **A shared top bar**, which the site did not have: wordmark left, the six sections right, the
  current one underlined in accent. The old three tabs could not carry seven views.
- Panels lose their 10px radius and their gaps, and become **ruled cells** — one outer border,
  hairline dividers between the two sides, matching the home page's scorecard grid.
- Labels become condensed uppercase with letter-spacing, so a form field reads like a scorebook
  column heading rather than a web form.
- Stat values use **tabular figures** so the right-hand column lines up.
- The **Predict** button becomes a square accent block with the step-and-press behaviour used
  across the site.

## Defects found and fixed in this round

1. **Crest colours stopped at the picker.** `.side.away .crest` only matched inside `.side`, so the
   same crest went grey in the stat panels. Now both contexts match.
2. **The card's glow bled onto the warm ground.** Two 80px team-colour glows plus a 56px black
   shadow read as a cool halo floating around the card. Tightened to 36px at 9%.
3. **The card's centre block collided with the team labels at 375px** — "Calibrated pregame model"
   ran straight through "RED SOX" and "DODGERS". The live app already solves this by pushing the
   block to the top of the card on narrow screens; reused that rule. Verified: 37px clear.

## Checks

**Contrast** — 11 pairs checked, all PASS:

| Pair | Ratio | Needs |
|---|---|---|
| away `#dd6348` on ground / panel | 5.25 / 4.90 | 3.0 |
| home `#79b0cc` on ground / panel | 7.84 / 7.33 | 3.0 |
| bar label on away / home segment | 5.39 / 8.05 | 4.5 |
| Predict button ink on accent | 5.39 | 4.5 |
| stat label muted on panel | 6.36 | 4.5 |
| stat value on panel | 14.25 | 4.5 |
| hitter line on panel-2 | 5.95 | 4.5 |
| nav muted on ground | 6.81 | 4.5 |

**Keyboard.** 19 focusable elements in reading order: wordmark, six nav links, away team, away
pitcher, three away hitters, home team, home pitcher, three home hitters, date, Predict. Nav
links, selects, the date input and the button all carry an explicit `:focus-visible` ring;
checkboxes use the browser's own.

**Layout.** 1280 (1803px), 768 (2669px), 375 (2987px). Single column from 820 down: the two sides
stack with a rule between them, the `@` is dropped, stat panels stack. At 480 the date field and
Predict go full width.

**Reduced motion.** All transitions disabled under `prefers-reduced-motion: reduce`.

## Known and expected

- Team crests are drawn as lettered circles. The live page loads real MLB logos from
  `primary_logo_url`; the mockup does not hotlink them.
- Nav links point at section ids that do not exist until M6.
- Not yet restyled: the "Calibrating…" progress bar and the error state. Both are part of this
  screen and belong in this round if you want them before M4.
