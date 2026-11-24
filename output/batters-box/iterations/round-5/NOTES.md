# Round 5 (M7b): the swing, direction C (Uniform), refined

**Date:** 2026-11-24
**Status:** approved 2026-11-24

## Files

| File | What it is |
|---|---|
| `swing-rig.js` | The rig. Everything between `rig:start` and `rig:end` ships; the review harness below it does not. |
| `check-rig.js` | Assert-based self-check. `build.py` runs it first and stops if it fails. |
| `build.py` | Swaps the five-layer CSS swing in `src/api/static/index.html` for the rig. With no argument it writes `index.html` here; at M7c it writes the source file. It refuses to run twice on the same file. |
| `index.html` | The candidate: today's app with the new swing in place. |
| `swing.html`, `swing.css` | Scrub page: today's swing beside this one, with a phase strip. |

## What changed since direction C

- **Shoes 30% → 40%** (2.27:1 → 3.10:1). **Socks 40% → 48%** (3.92:1), so they still read darker than the pants.
- **Bat lowered 4–6° in stance, load and plant.** The self-check caught the tip touching the diagram's top edge during the load.
- **Uniform only.** The chalk and strobe branches are gone, and the rig sits in one scope (`BatterRig`), so none of its helper names (`add`, `el`, `pose` …) can collide with the app's globals.
- **Keyframe table tidied** into aligned columns.

## How it joins the page (in `index.html`)

- **CSS:** the old rig's rules (`.b-dim`, `.b-fill`, `.bat-*`, `.b-stroke`, `.b-swing`, `.b-arc`, `.b-reach`, `.b-body`, `.batter`) are replaced by `.r-limb`, `.r-solid`, `.r-handle`, `.r-barrel`, `.r-trail` and `.r-belt`. Every tone is mixed with `color-mix()` from `--chalk` into `--ground`, so no new colour token is needed.
- **Markup:** the hand-drawn figure becomes an empty `<g class="batter">` that the rig draws into on load. The contact burst moves to its own `<g class="burst-at">`, placed on the rig's contact point.
- **JS:** `swingBatter(hit)` runs the swing on `requestAnimationFrame` from the release and holds the finish. Only one swing runs at a time.
- **Contact point:** `CONTACT_POINT` comes from the rig, at (277.7, 216.5) with scale 0.91, instead of the hand-measured (264, 239).
- **Reset:** `showTab()` calls `resetBatter()`, so the batter is back in his stance when you return home.
- **Removed:** the seven WAAPI swing animations, `SWING_TOTAL` and `CONTACT_FRAC`.

## Checks

| Check | Result |
|---|---|
| Self-check (every 2 ms of the swing) | Hands always on the bat. Legs always reach their feet. Every point inside the viewBox. Contact inside the zone. Swing clock never runs backwards. Fastball met at 900 ms, off-speed early. |
| Click path, 1280 | Swing runs. Ball lands on (277.7, 216.5) at scale 0.91. Burst peaks at 0.92 opacity on the fastball. "Strike" reaches 1.0 on the changeup. Navigates to `#predict` / `#model`. Stance is restored on return. |
| Reduced motion | No swing. Navigates after 6 ms. |
| 1280 / 768 / 375 | Figure scales with the diagram. No horizontal overflow at 375 (scroll width = 375). See `shots/m7-r5-*`. |
| Console | Only the expected 404s, because the static preview has no API behind it. Run against the real API at M7c. |

**Contrast** against `--ground` `#16130f`:

| Part | Ratio |
|---|---|
| Gloves | 13.39:1 |
| Arms | 9.25:1 |
| Jersey | 7.36:1 |
| Pants | 4.90:1 |
| Barrel | 5.25:1 |
| Socks | 3.92:1 |
| Helmet | 3.70:1 |
| Shoes | 3.10:1 |

Every part now clears 3:1.

## The still pose (Decision Point 3)

`shots/m7-r5-stance-vs-today.png` shows the change on page load. The batter is slimmer, crouched and side-on, in uniform tones, and the bat is a real 34-inch length. Today's figure is upright, one-tone and cartoon-proportioned. This needs the user's approval before M7c.
