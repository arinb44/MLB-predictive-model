# Design Plan — Batter's Box

**Agent:** Strike Zone (`output/batters-box/designAgent.md`)
**Project:** MLB Game Outcome Predictor — `/Users/arins/Documents/Projects/BaseballModel`
**Date:** 2026-11-20
**Status:** Awaiting approval

---

## Project Title

**Batter's Box** — a home page where every section of the MLB predictor is a pitch, and a restyle of the app behind it.

## Objective

The app works but looks like a default dark dashboard: cool slate panels, system sans, three unlabelled tabs. This project gives it an identity. A new landing page puts a batter at the plate in front of a strike zone, with six pitches placed in and around the zone — each pitch is a section of the site. The three existing screens keep their layouts and logic and take on the new palette, type and panel style. The result should read as the sibling of *Fourth and Why*, by the same hand, without reusing its colors.

## Users & Context

- **Primary:** recruiters and people browsing the GitHub repo, who will look at the landing page for a few seconds and may never click past it. The home page has to carry the whole impression on its own.
- **Secondary:** baseball fans using the predictor — they arrive to pick two teams and get a number, and must not be slowed down by decoration.
- **Context:** desktop and laptop mostly, phone often enough to matter. Served by FastAPI at `GET /`, so the page is instant — no loading screen, unlike the Pyodide-backed NFL site.

## Design Requirements

1. **The home page is a batter's box.** A batter figure at the plate, a strike zone, and six pitch marks positioned in and around that zone. Not a stadium scene — a diagram, the way a pitch chart is a diagram.
2. **Every pitch is a section.** Each of the six marks is a labelled, clickable tile carrying the section name and a one-line description, mirroring how *Fourth and Why* labels each tile with a football position.
3. **Six sections:** Predictions, Players, Teams, Model, Matchups, About the data.
4. **Each pitch has a pitch type.** Fastball, slider, curveball, changeup, sinker, cutter — assigned so the mapping is defensible, not random (see Decision Points).
5. **Own palette.** A warm dark ground and one accent, distinct from the NFL site's `#14110f` / `#e3a83c`. No team color may dominate; the site belongs to no club.
6. **Own type pairing.** A serif or condensed display face over a workhorse sans, free for web use via Google Fonts. The current Barlow Condensed link is loaded but barely used — either commit to it or replace it.
7. **Tokens defined once.** All color, type-scale and spacing values live in the page's `:root` as CSS custom properties. No hard-coded hex anywhere else, including in the JS that builds charts.
8. **Restyle, don't rebuild.** Predictions, Players and Teams keep their current structure, controls and chart logic. Only surface styling changes.
9. **Honesty preserved.** The existing notes that distinguish model inputs (team form, Elo, trailing starter proxy) from display-only context must survive the restyle, and the About page should make that distinction plainly.
10. **Accessible.** WCAG 2.2 AA. Pitch tiles reachable and operable by keyboard, with a visible focus ring. Motion respects `prefers-reduced-motion`.
11. **One file, no build.** Everything ships inside `src/api/static/index.html`: inline `<style>`, inline SVG, vanilla JS. No npm, no bundler, no new dependency.

## Scope

**In scope**
- New home / batter's-box page, including the batter, strike zone and pitch SVGs.
- A name and serif wordmark for the site, if the user picks one from the candidates.
- Design tokens as CSS custom properties.
- Restyle of Predictions, Players and Teams — palette, type, panels, controls, chart colors.
- Three new content pages: Model, Matchups, About the data.
- Navigation that connects all seven views.

**Out of scope**
- The FastAPI backend: routes, schemas, model pipeline, feature building, training, evaluation.
- Chart logic — which stats are plotted, how they rank, where the data comes from.
- The lineup-picking flow and the `/predict` payload shape.
- Data files, `config.yaml`, the Dockerfile, CI.
- New backend routes or a `StaticFiles` mount, unless separately approved.
- Light mode. The site is dark only.

## Deliverables

| Deliverable | Format | Where |
|---|---|---|
| Design directions (3) | Standalone HTML pages, viewable in the browser | `output/batters-box/directions/direction-{a,b,c}.html` |
| Refinement rounds | HTML pages per round | `output/batters-box/iterations/round-<n>/` |
| Design tokens | CSS custom properties | `output/batters-box/final/tokens.css`, then the `:root` block of `index.html` |
| SVG assets | Inline SVG (batter, strike zone, pitch marks, wordmark) | `output/batters-box/final/assets.svg` as the source of truth, inlined into `index.html` |
| Final page | The edited app | `src/api/static/index.html` — only after approval and a confirmed path |
| Record of the work | Markdown | `output/batters-box/design-spec.md` (process record, not a shipped deliverable) |

No Figma files on this project.

## Design Process

1. **Tokens first.** Each direction is a complete token set — ground, panel, rule, text, muted, accent, type scale — not just a look. Picking a direction picks a system.
2. **Three directions, same content.** The identical home page built three ways, so the comparison is about the design rather than about which one got more effort. Each gets its concept, hex values, fonts, strengths and weaknesses written out.
3. **Shown in the browser.** Served from a local preview so they can be opened side by side, at desktop and mobile widths.
4. **Refine in rounds.** The chosen direction is developed milestone by milestone, each round saved and reviewed. Nothing is marked approved without the user saying so.
5. **One lead skill.** `/design-taste-frontend` leads the HTML/CSS direction work; `/emil-design-eng` advises on component detail and states during refinement. They are not stacked on the same piece of work.
6. **Checks each round.** Contrast ratios computed and reported as actual numbers; layout checked at each breakpoint; keyboard path walked.

## Accessibility & Responsiveness

- **Standard:** WCAG 2.2 AA — 4.5:1 for body text, 3:1 for large text (≥24px, or ≥19px bold) and for UI component boundaries and focus indicators.
- **Breakpoints:** 375px (mobile), 768px (tablet), 1280px (desktop). The strike-zone grid reflows to a stacked list on mobile rather than shrinking until the labels break.
- **Color mode:** dark only.
- **Keyboard:** pitch tiles are anchors or buttons with a visible focus ring, in a sensible tab order. Tabs keep their existing `role="tablist"` semantics.
- **Motion:** any pitch-path or entrance animation is short, non-looping, and disabled under `prefers-reduced-motion: reduce`.
- **Color independence:** home/away and chart series stay distinguishable without relying on hue alone — position, labelling or weight carry the difference too.

## Milestones

| # | Milestone | Output |
|---|---|---|
| **M1** | Three home-page directions, each a full token set, plus name and wordmark candidates | `directions/` |
| **M2** | Chosen direction refined: home page final at 375 / 768 / 1280, contrast report, keyboard pass | `iterations/round-1/` |
| **M3** | Predictions restyled | `iterations/round-2/` |
| **M4** | Players and Teams restyled, including chart colors in the JS | `iterations/round-3/` |
| **M5** | New pages: Model, Matchups, About the data | `iterations/round-4/` |
| **M6** | Everything merged into `src/api/static/index.html`, final assets and tokens saved, spec written, commit offered | `final/`, `src/api/static/index.html` |

Each milestone ends with a review and needs approval before the next begins.

## Decision Points

1. **Which direction** (M1) — the one that sets palette, type and the whole token system.
2. **The name** (M1) — candidates shown as serif wordmarks in the hero, or keep "MLB Game Outcome Predictor".
3. **Pitch-to-section mapping** (M1) — proposed starting point, open to change:

   | Pitch | Section | Why |
   |---|---|---|
   | Four-seam fastball | Predictions | The main event, straight down the middle |
   | Slider | Players | Breaks away — individual lines, off the main axis |
   | Curveball | Teams | The big arc — the season-long shape |
   | Changeup | Model | The pitch that explains the others; deception made legible |
   | Sinker | Matchups | Low in the zone, ground-level detail |
   | Cutter | About the data | Late, small movement — the fine print |

4. **What Matchups contains** (before M5) — currently the only tile with no existing content behind it. Options: (a) a head-to-head history view between two teams; (b) today's slate with a predicted probability per game; (c) drop it and ship five pitches. This needs an answer before M5, and (b) may need a backend route, which is out of scope.
5. **Chart restyle depth** (M4) — recolor only, or also adjust dot size, gridline weight and label placement.
6. **The source-tree write** (M6) — exact confirmation before `src/api/static/index.html` is edited.
7. **Git** (M6) — which repository, and whether to push.

## Risks & Limitations

- **One file, growing.** `index.html` is already 1,250 lines with inline CSS and JS. Adding a home page and three sections could push it past 2,000. There is no build step to split it, and splitting would need a `StaticFiles` mount, which is out of scope. The file stays monolithic; the mitigation is strict token discipline and clear section comments.
- **Chart colors live in JS.** The charts are built by hand-written JS that emits SVG. "Restyle, don't rebuild" still means editing that code to read CSS variables instead of literals. This is the most likely place for the restyle to break something; M4 is the risky milestone.
- **No static mount.** SVG assets must be inlined. That costs page weight and makes the file longer, but avoids a backend change.
- **No brand assets exist.** There is no logo, no palette, no typeface of the user's. Everything is being invented, so M1 carries more weight than usual.
- **Remote team logos.** Logos are fetched from MLB's servers at display time. They are full-color and will sit on a warm dark ground — some will clash, and none can be recolored. The design has to frame them rather than fight them.
- **Three new pages is real work.** Model, Matchups and About roughly double the content surface. Matchups is the weakest of the three and is the first thing to cut if the project needs to shrink.
- **Pitch metaphor can over-reach.** If every element becomes a baseball pun the page stops being readable. The metaphor stays on the home page; the data screens are plain.

## Open Questions

1. **Matchups** — what should it actually show? (Decision Point 4; needed before M5, not before M1.)
2. **GitHub repository** — is `origin https://github.com/arinb44/MLB-predictive-model.git` the right destination for commits? Nothing is committed until this is answered.
3. **Inline SVG** — confirmed as the approach, or add a `StaticFiles` mount to `src/api/main.py` and ship real asset files?
4. **The design spec** — keep it as a record in `output/`, or skip it?

None of these block M1.

---

**Status:** Awaiting approval
