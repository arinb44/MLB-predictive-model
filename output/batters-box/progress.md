# Progress — batters-box

**Current phase:** Phase 4 — M7, a realistic swing (scope added on resume, 2026-11-24)
**Status:** complete — M7 pushed as `f1270d0`; the tile numbers removed and the CI runner pinned to Ubuntu 24.04 on 2026-11-24. M1–M7 and Phase 5 are complete.

## Completed milestones
- **2026-11-20** — Phase 0: project root confirmed (`/Users/arins/Documents/Projects/BaseballModel`); no earlier design projects found.
- **2026-11-20** — Phase 1a: read-only survey of the project and of the NFL reference site.
- **2026-11-20** — Phase 1b/1c: three setup questions and deliverables answered; follow-ups on pitch count and naming answered; slug `batters-box` proposed.
- **2026-11-20** — Phase 2: `output/batters-box/designAgent.md` written and approved by the user.
- **2026-11-20** — Phase 3: `plan.md` written and approved by the user.
- **2026-11-20** — The site's name chosen: **Full Count**.
- **2026-11-20** — M1 complete: three directions built and checked; the user chose **A — Scorebook**.
- **2026-11-20** — M2 complete: `iterations/round-1/home.html` approved by the user.
- **2026-11-20** — M3 complete: `iterations/round-2/predictions.html` approved.
- **2026-11-20** — M4 complete: `iterations/round-3/` approved.
- **2026-11-20** — Matchups defined as head-to-head history.
- **2026-11-20** — M5: `iterations/round-4/` built — Model, Matchups and About the data.
- **2026-11-20** — Head-to-head route approved; contract written to `iterations/round-4/head-to-head-endpoint.md`.
- **2026-11-20** — Real MLB logos put back across rounds 2, 3 and 4; all three pages 0 FAIL on `perf.mjs`.
- **2026-11-20** — M5 approved.
- **2026-11-20** — **M6 complete:** merged into `src/api/static/index.html` (7 views), added `GET /head-to-head/{a}/{b}` to `src/api/main.py`, updated `tests/test_api.py`. Verified against the running app; 25/25 tests pass.
- **2026-11-20** — Phase 5: `design-spec.md`, `final/tokens.css`, `final/batters-box.svg` written.
- **2026-11-20** — Follow-up, pushed as `e9ac649`: contact burst on the fastball, "Strike" callout on every miss, and a one-second hold before the section opens.
- **2026-11-20** — Follow-up, pushed as `1a356e9`: the batter's box animates. Hitter redrawn from the umpire's view with stacked legs; five-layer swing rig (hips, shoulders, bat arc, arm extension, barrel trail); dotted balls hidden until a pitch is thrown; 900ms travel.
- **2026-11-24** — Resumed for M7 (a realistic swing). Root and repository re-confirmed. Stale record fixed: `plan.md` status set to approved on 2026-11-20, open question 2 struck. Current swing captured frame by frame into `shots/m7-before-*.png`. M7 added to `designAgent.md`; addendum appended to `plan.md`.
- **2026-11-24** — M7 addendum approved (slow motion ×2.1). M7a built: `directions/swing-rig.js`, `swing.css`, `swing-{a,b,c}.html`; strips and before/after shots in `shots/m7-*`. Notes in `directions/README.md`.
- **2026-11-24** — User chose **C — Uniform**. Round 5 built in `iterations/round-5/`: refined rig, self-check, `build.py`, candidate `index.html`, scrub page. Checked at 1280/768/375 and with reduced motion; shoes raised to 3.10:1. Notes in `iterations/round-5/NOTES.md`.
- **2026-11-24** — Round 5 approved, including the new still pose. The user then asked for spinning balls with no numbers or dotted outline; built as round 6 in `iterations/round-6/` on top of round 5.
- **2026-11-24** — Round 6 approved. **M7c:** `iterations/round-6/build.py` wrote `src/api/static/index.html` (1930 → 2109 lines). Verified against the running API: fastball swung and met with the burst, changeup swung early with "Strike", sections open, stance restored, seams spin, no console errors; 25/25 tests pass. `design-spec.md` gained §10; `final/batters-box.svg` re-exported from the page by `iterations/round-6/export-svg.js` (stance matches the live page path for path).
- **2026-11-24** — M7 committed and **pushed** to `arinb44/MLB-predictive-model` as `f1270d0` on `main` (42 files; `.claude/` left out). No AI markers in the message; author unchanged.
- **2026-11-24** — The 1–6 removed from the pitch tiles at the user's request (decision 33). 25/25 tests pass; checked on the running app.
- **2026-11-24** — The user reported the GitHub `Tests / pytest` check failing. Cause: `ubuntu-latest` is now Ubuntu 26.04, which has no Python 3.9 build, so setup fails before pytest runs; every push since `bfc6f4a` (2026-11-20) is red. Not caused by M7. Fixed, with the user's approval, by pinning `.github/workflows/tests.yml` to `ubuntu-24.04`.
- **2026-11-20** — Committed and **pushed** to `arinb44/MLB-predictive-model` as `bfc6f4a` on `main`. The first push was rejected because this checkout's `main` was a parallel rewrite of the remote's history (same 11 subjects, different hashes and dates, identical trees); the user rebased the single unpushed commit onto `origin/main`, which resolved it. 25/25 tests pass on the rebased commit.

## Next step
None required.

## Open questions
1. ~~Should `output/` be committed?~~ — **committed and pushed** as `3b7bbe0`, with `.profile/` and `.taste-skill/` gitignored. `.claude/` stays local.
2. ~~Which GitHub repository should commits go to?~~ — **`arinb44/MLB-predictive-model`, `main`** (decision 21; re-confirmed 2026-11-24).
3. ~~Approve the head-to-head route~~ — **approved**; contract in `iterations/round-4/head-to-head-endpoint.md`, implemented at M6.
4. SVG assets inlined into `index.html` (no static mount exists), or add `StaticFiles` to `src/api/main.py`? The same answer decides whether the Model page can show `reports/shap_*.png`.
5. Keep `design-spec.md` as a record in `output/`, or skip it?
6. Lighten the hairline rules to 3:1, or leave them decorative?
7. Restyle the "Calibrating…" bar and the error state now, or in a later round?
8. The Predictions subtitle says only team form, Elo and the starter proxy drive the number; the README and `get_feature_columns` describe a wider set (rest, bullpen fatigue, park factors, pitcher identity). Which is accurate?

**Last updated:** 2026-11-24
