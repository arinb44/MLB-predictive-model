# Progress — batters-box

**Current phase:** Phase 5 — Final delivery
**Status:** complete. Everything is pushed, including this design project.

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
- **2026-11-20** — Committed and **pushed** to `arinb44/MLB-predictive-model` as `bfc6f4a` on `main`. The first push was rejected because this checkout's `main` was a parallel rewrite of the remote's history (same 11 subjects, different hashes and dates, identical trees); the user rebased the single unpushed commit onto `origin/main`, which resolved it. 25/25 tests pass on the rebased commit.

## Next step
None outstanding. The redesign, the animation and this design project are all
on `main` at `arinb44/MLB-predictive-model`.

## Open questions
1. ~~Should `output/` be committed?~~ — **committed and pushed** as `3b7bbe0`, with `.profile/` and `.taste-skill/` gitignored. `.claude/` stays local.
2. Which GitHub repository should commits go to? (Existing remote: `origin https://github.com/arinb44/MLB-predictive-model.git`.) Nothing is committed until answered.
3. ~~Approve the head-to-head route~~ — **approved**; contract in `iterations/round-4/head-to-head-endpoint.md`, implemented at M6.
4. SVG assets inlined into `index.html` (no static mount exists), or add `StaticFiles` to `src/api/main.py`? The same answer decides whether the Model page can show `reports/shap_*.png`.
5. Keep `design-spec.md` as a record in `output/`, or skip it?
6. Lighten the hairline rules to 3:1, or leave them decorative?
7. Restyle the "Calibrating…" bar and the error state now, or in a later round?
8. The Predictions subtitle says only team form, Elo and the starter proxy drive the number; the README and `get_feature_columns` describe a wider set (rest, bullpen fatigue, park factors, pitcher identity). Which is accurate?

**Last updated:** 2026-11-20
