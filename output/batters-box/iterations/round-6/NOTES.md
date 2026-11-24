# Round 6 (M7b, continued): spinning balls

**Date:** 2026-11-24
**Status:** approved 2026-11-24
**Asked for by the user:** "make the balls spin and remove the numbers, also remove the dotted lines around the ball"

## What changed (on top of the approved round 5)

- **No dotted outline and no number.** Each ball is a solid `--chalk` disc (`.ball-body`) with one red seam (`.ball-seam`). The pitch tiles keep their 1–6. Only the numbers printed on the balls are gone.
- **The balls spin.** The seam is the real baseball curve on a sphere (`a = 0.7, b = 0.3`), turned about each pitch's spin axis and redrawn each frame where it faces the camera:

  | Pitch | Spin | Axis (catcher's view) | rpm |
  |---|---|---|---|
  | 1 Four-seam | backspin, a touch arm-side | (-0.97, -0.24, 0) | 2300 |
  | 2 Slider | mostly gyro, the spinning dot | (0.35, 0.10, 0.93) | 2450 |
  | 3 Curveball | topspin | (0.98, 0.20, 0) | 2500 |
  | 4 Changeup | backspin tilted arm-side | (-0.80, -0.56, 0.20) | 1750 |
  | 5 Sinker | mostly sidespin | (-0.60, -0.76, 0.25) | 2150 |
  | 6 Cutter | gyro, a little backspin | (0.30, -0.30, 0.90) | 2400 |

- **Spin speed.** The relative rates are real, but the spin is slowed further than the flight. A 2,300 rpm fastball makes about 2.2 turns on its way in (`SPIN_TURNS`), because at the true rate it would only be a blur at any frame rate.
- **Stops when caught.** A missed pitch stops spinning when it reaches its spot. The fastball keeps spinning off the bat until it leaves the frame.
- **Housekeeping.** The diagram's label now reads "six pitches", not "six numbered pitches". The dead `.ball:focus-visible` rules are removed, since the balls aren't focusable.

## Files

- `build.py` runs `../round-5/build.py` into the same path, then edits the balls. `python3 build.py src/api/static/index.html` is the M7c command.
- `index.html` is the candidate.
- `export-svg.js` (`node export-svg.js`) rewrites `final/batters-box.svg` from `src/api/static/index.html`: the home diagram with the rig's stance and the seams drawn in, as the page shows it on load.

## Checks

| Check | Result |
|---|---|
| Curveball (miss) | 55 distinct seam frames during travel; stops at 899 ms. |
| Fastball (hit) | 88 distinct seam frames through travel and flight; stops at 1432 ms. |
| Looks | `shots/m7-r6-six-balls.png` (all six axes), `shots/m7-r6-contact-ball.png` (contact). |
| Contrast | Ball body against the ground 13.39:1. Seams against the ball 2.55:1. |
| Script | Parses. Round 5's self-check passes as part of the build. |

The seams fall below 3:1 against the ball. They are decoration inside a 13.39:1 shape on an `aria-hidden` element, so nothing depends on seeing them. Darkening them to pass would mean leaving `--accent`.
