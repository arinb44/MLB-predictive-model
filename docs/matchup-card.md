# Matchup Card — Build Guide

A reusable "Away @ Home" matchup card: a dark split card where each team's real
logo fades in from its own edge, lit by a glow in the team's color, with the
result (e.g. win probabilities) in the center. It ships with an optional
**"Calibrating…"** progress bar that holds for a minimum time before the card
is revealed.

Originally built for the MLB Game Outcome Predictor
(github.com/arinb44/MLB-predictive-model), adapted from the Figma Make
template *"Design baseball team image card."* Everything below is framework-free
HTML/CSS/JS, so it drops into any project; a React port is at the end.

---

## 1. What it looks like

```
┌─────────────────────────────┬─────────────────────────────┐
│ LOGO ▓▓▒▒░░                 │                 ░░▒▒▓▓ LOGO │
│ (away glow)       [ WIN PROBABILITY ]         (home glow) │
│                    53.3%    │    46.7%                    │
│                        TUE · SEP 22                       │
│ LOS ANGELES     Calibrated pregame model          CHICAGO │
│ DODGERS                     │                        CUBS │
│ LAD                         │                         CHC │
│                WRIGLEY FIELD · CHICAGO, IL                │
└─────────────────────────────┴─────────────────────────────┘
  away team (left)     hairline divider      home team (right)
  logos fade in from each outer edge toward the center
```

## 2. Anatomy: the layer stack

The card is one `position: relative; overflow: hidden` box with absolutely
positioned layers. The z-order matters, because the labels have to sit above
the logos and the grain has to sit above everything:

| z | Layer | What it does |
|---|-------|--------------|
| 1 | `.mc-half.away` / `.mc-half.home` | Each covers 50% of the width and holds that team's glow, logo, and labels |
| – | ↳ `.mc-glow` | Radial gradient in the team color, anchored near the outer edge (20% / 80%) |
| – | ↳ `.mc-logo-wrap` | 60% of the half's width, with a **CSS mask** so the logo is solid at the edge and transparent toward the center |
| 10 | ↳ `.mc-label` | City / nickname / abbreviation, pinned to the bottom corner |
| 5 | `.mc-divider` | 1px vertical line at 50%, faded at the top and bottom |
| 8 | `.mc-center` | Pill, the two percentages, date, and subtitle, centered on the divider |
| 9 | `.mc-venue` | Ballpark line along the bottom edge |
| 10 | `.mc-grain` | SVG fractal-noise texture at 3% opacity, which keeps the dark background from looking flat |

### The three techniques that make it work

1. **Edge fade = `mask-image`, not opacity.** A linear-gradient mask
   (`#000 0% → 0.85 30% → 0.4 60% → transparent 100%`) makes the logo dissolve
   toward the center, so the two logos never collide. Always include the
   `-webkit-mask-image` duplicate, because Safari still needs it.
2. **One color variable per side drives everything.** Set `--away-c` and
   `--home-c` on the card and derive every tint with `color-mix()`: 33% for
   the glow, 53% for the logo's drop-shadow, 13% for the outer box-shadow,
   and a lightened 65%-with-white for the abbreviation. Swapping teams only
   means changing two variables.
3. **Logo variants built for dark backgrounds.** Many team logos use a dark
   primary color (Yankees navy, Tigers navy) that disappears on a near-black
   card. Use a logo variant made for dark backgrounds (see §5).

## 3. Design tokens

| Token | Value |
|---|---|
| Card size | `height: 320px` (290px under 720px wide), width fluid |
| Radius | `16px` |
| Background | `linear-gradient(135deg, #0a0a12 0%, #111118 50%, #0a0a12 100%)` |
| Card shadow | `0 0 0 1px rgba(255,255,255,.06), 0 32px 64px rgba(0,0,0,.7)`, plus an 80px glow per team at 13% |
| Font | **Barlow Condensed** 600/700/800/900 (Google Fonts) |
| Nickname | 36px / 900 / uppercase / `letter-spacing: -0.025em` |
| City | 12px / 600 / uppercase / `0.1em` / white at 55% |
| Abbreviation | 14px / 700 / `0.1em` / team color mixed 65% with white, glow `drop-shadow(0 0 8px color)` |
| Percentages | 44px / 800 / tabular numbers; the favorite gets a colored `text-shadow` |
| Pill | 12px / 700 / `0.1em`, `rgba(255,255,255,.07)` fill, `.12` border, `.5` text |
| Logo | 208×208 (140×140 on mobile), 90% opacity |

## 4. Step-by-step build

1. **Card shell.** Make a relative, overflow-hidden box with the gradient
   background, a 16px radius, and the layered box-shadow.
2. **Split into halves.** Add two absolutely positioned 50%-wide columns.
   Each is a flex column with `justify-content: flex-end` and
   `padding-bottom: 28px`, so the labels sit at the bottom.
3. **Glow.** Inside each half, add a full-size div with a
   `radial-gradient(at 20% 50%, color 33%, transparent 70%)`. Mirror it to
   `80%` on the home side.
4. **Logo and mask.** Add a 60%-wide wrapper anchored to the outer edge,
   vertically centered, with the linear-gradient mask pointing toward the
   center. Put the logo `<img>` inside with a colored drop-shadow.
5. **Labels.** Stack the city, nickname, and abbreviation. Mirror the home
   side (`align-items: flex-end; text-align: right`).
6. **Divider.** Add a 1px line at `left: 50%` with a
   `linear-gradient(transparent, white 30%, white 70%, transparent)` at 20%
   opacity.
7. **Center block.** Add a full-card flex column centered both ways, with
   `pointer-events: none`. It holds the pill, a 2-column grid of
   percentages (away right-aligned and home left-aligned, so they sit on
   either side of the divider), the date, and the subtitle.
8. **Venue and grain.** Add the bottom-centered venue text, then the noise
   layer on top.
9. **Reveal.** Count the percentages up from 0 with an ease-out curve over
   about 700ms, and mark the favorite.
10. **Mobile (under 720px).** Use a 290px card and 140px logos, top-align the
    center block (`padding-top: 22px`) so it clears the bottom labels, shrink
    the type, and hide the venue line.

## 5. Data you need per team

```js
{
  code: "NYY",                 // shown as the abbreviation
  city: "New York",            // small label above the nickname
  nickname: "Yankees",         // big label
  color: "#0C2340",            // primary brand color; drives the glow and tints
  logo: "https://…/147.svg",   // large logo, ideally a version made for dark backgrounds
  venue: "Yankee Stadium · Bronx, NY"   // home team only
}
```

**MLB logos.** MLB serves official SVGs keyed by MLB team ID:

- Large and faded (use this for the card): `https://www.mlbstatic.com/team-logos/team-primary-on-dark/{id}.svg`
- Compact cap logo (small icons): `https://www.mlbstatic.com/team-logos/team-cap-on-dark/{id}.svg`

These are hotlinked, not bundled. That keeps the repo light, but the
images need network access and belong to MLB, so check the usage terms for
anything beyond a personal or portfolio project.

<details>
<summary>All 30 MLB teams: ID, color, city, 2026 ballpark</summary>

| Code | MLB ID | Color | City | Ballpark |
|---|---|---|---|---|
| ARI | 109 | #A71930 | Arizona | Chase Field · Phoenix, AZ |
| ATL | 144 | #CE1141 | Atlanta | Truist Park · Atlanta, GA |
| BAL | 110 | #DF4601 | Baltimore | Camden Yards · Baltimore, MD |
| BOS | 111 | #BD3039 | Boston | Fenway Park · Boston, MA |
| CHC | 112 | #0E3386 | Chicago | Wrigley Field · Chicago, IL |
| CHW | 145 | #27251F | Chicago | Rate Field · Chicago, IL |
| CIN | 113 | #C6011F | Cincinnati | Great American Ball Park · Cincinnati, OH |
| CLE | 114 | #00385D | Cleveland | Progressive Field · Cleveland, OH |
| COL | 115 | #333366 | Colorado | Coors Field · Denver, CO |
| DET | 116 | #0C2340 | Detroit | Comerica Park · Detroit, MI |
| HOU | 117 | #EB6E1F | Houston | Daikin Park · Houston, TX |
| KCR | 118 | #004687 | Kansas City | Kauffman Stadium · Kansas City, MO |
| LAA | 108 | #BA0021 | Los Angeles | Angel Stadium · Anaheim, CA |
| LAD | 119 | #005A9C | Los Angeles | Dodger Stadium · Los Angeles, CA |
| MIA | 146 | #00A3E0 | Miami | loanDepot park · Miami, FL |
| MIL | 158 | #12284B | Milwaukee | American Family Field · Milwaukee, WI |
| MIN | 142 | #002B5C | Minnesota | Target Field · Minneapolis, MN |
| NYM | 121 | #FF5910 | New York | Citi Field · Queens, NY |
| NYY | 147 | #0C2340 | New York | Yankee Stadium · Bronx, NY |
| OAK/ATH | 133 | #003831 | Sacramento | Sutter Health Park · Sacramento, CA |
| PHI | 143 | #E81828 | Philadelphia | Citizens Bank Park · Philadelphia, PA |
| PIT | 134 | #FDB827 | Pittsburgh | PNC Park · Pittsburgh, PA |
| SDP | 135 | #2F241D | San Diego | Petco Park · San Diego, CA |
| SEA | 136 | #0C2C56 | Seattle | T-Mobile Park · Seattle, WA |
| SFG | 137 | #FD5A1E | San Francisco | Oracle Park · San Francisco, CA |
| STL | 138 | #C41E3A | St. Louis | Busch Stadium · St. Louis, MO |
| TBR | 139 | #092C5C | Tampa Bay | Tropicana Field · St. Petersburg, FL |
| TEX | 140 | #003278 | Texas | Globe Life Field · Arlington, TX |
| TOR | 141 | #134A8E | Toronto | Rogers Centre · Toronto, ON |
| WSN | 120 | #AB0003 | Washington | Nationals Park · Washington, DC |

Codes are Baseball-Reference style. The MLB Stats API uses AZ, CWS, KC, SD,
SF, TB, WSH, and ATH instead.
</details>

**Other sports.** Nothing in the component is baseball-specific. Feed it any
two teams with a color and a logo. ESPN's CDN, for example, serves league
logos at `https://a.espncdn.com/i/teamlogos/{league}/500/{abbr}.png` (check
the terms).

## 6. The code: a copy-paste component

### 6a. Font (in `<head>`)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&display=swap" rel="stylesheet">
```

### 6b. CSS

```css
/* ---------- Matchup card ---------- */
.mc {
  --away-c: #888; --home-c: #888;
  position: relative; overflow: hidden; border-radius: 16px; height: 320px; user-select: none;
  background: linear-gradient(135deg, #0a0a12 0%, #111118 50%, #0a0a12 100%);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.06), 0 32px 64px rgba(0,0,0,0.7),
              0 0 80px color-mix(in srgb, var(--away-c) 13%, transparent),
              0 0 80px color-mix(in srgb, var(--home-c) 13%, transparent);
  font-family: "Barlow Condensed", sans-serif;
}
.mc-grain {
  position: absolute; inset: 0; opacity: 0.03; pointer-events: none; z-index: 10; background-size: 128px auto;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}
.mc-divider {
  position: absolute; top: 0; bottom: 0; left: 50%; width: 1px; transform: translateX(-50%); opacity: 0.2; z-index: 5;
  background: linear-gradient(transparent, white 30%, white 70%, transparent);
}
.mc-half { position: absolute; top: 0; bottom: 0; width: 50%; display: flex; flex-direction: column;
           justify-content: flex-end; padding-bottom: 28px; z-index: 1; }
.mc-half.away { left: 0;  --c: var(--away-c); }
.mc-half.home { right: 0; --c: var(--home-c); align-items: flex-end; }
.mc-glow { position: absolute; inset: 0; }
.mc-half.away .mc-glow { background: radial-gradient(at 20% 50%, color-mix(in srgb, var(--c) 33%, transparent) 0%, transparent 70%); }
.mc-half.home .mc-glow { background: radial-gradient(at 80% 50%, color-mix(in srgb, var(--c) 33%, transparent) 0%, transparent 70%); }
.mc-logo-wrap { position: absolute; top: 0; bottom: 0; width: 60%; display: flex; align-items: center; }
.mc-half.away .mc-logo-wrap {
  left: 0; padding-left: 32px;
  -webkit-mask-image: linear-gradient(to right, #000 0%, rgba(0,0,0,0.85) 30%, rgba(0,0,0,0.4) 60%, transparent 100%);
          mask-image: linear-gradient(to right, #000 0%, rgba(0,0,0,0.85) 30%, rgba(0,0,0,0.4) 60%, transparent 100%);
}
.mc-half.home .mc-logo-wrap {
  right: 0; padding-right: 32px; justify-content: flex-end;
  -webkit-mask-image: linear-gradient(to left, #000 0%, rgba(0,0,0,0.85) 30%, rgba(0,0,0,0.4) 60%, transparent 100%);
          mask-image: linear-gradient(to left, #000 0%, rgba(0,0,0,0.85) 30%, rgba(0,0,0,0.4) 60%, transparent 100%);
}
.mc-logo { width: 208px; height: 208px; object-fit: contain; opacity: 0.9;
           filter: drop-shadow(0 0 32px color-mix(in srgb, var(--c) 53%, transparent)); }
.mc-label { position: relative; z-index: 10; padding: 0 28px; display: flex; flex-direction: column; }
.mc-half.home .mc-label { align-items: flex-end; text-align: right; }
.mc-city { font-size: 12px; line-height: 16px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;
           color: rgba(255,255,255,0.55); margin-bottom: 2px; }
.mc-name { font-size: 36px; line-height: 1; font-weight: 900; letter-spacing: -0.025em; text-transform: uppercase; color: #fff; }
.mc-abbr { font-size: 14px; line-height: 20px; font-weight: 700; letter-spacing: 0.1em; margin-top: 4px; text-transform: uppercase;
           color: color-mix(in srgb, var(--c) 65%, white); filter: drop-shadow(0 0 8px var(--c)); }
.mc-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center;
             justify-content: center; gap: 8px; z-index: 8; pointer-events: none; }
.mc-pill { padding: 2px 12px; border-radius: 999px; font-size: 12px; line-height: 16px; font-weight: 700; letter-spacing: 0.1em;
           text-transform: uppercase; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12);
           color: rgba(255,255,255,0.5); margin-bottom: 4px; }
.mc-odds { display: grid; grid-template-columns: 1fr 1fr; gap: 36px; align-items: baseline; }
.mc-pct { font-size: 44px; font-weight: 800; line-height: 1; color: #fff; font-variant-numeric: tabular-nums; }
.mc-pct.away { text-align: right; --c: var(--away-c); }
.mc-pct.home { --c: var(--home-c); }
.mc-pct.fav  { text-shadow: 0 0 18px color-mix(in srgb, var(--c) 70%, white); }
.mc-date { font-size: 14px; line-height: 20px; font-weight: 700; letter-spacing: 0.1em; color: #fff; opacity: 0.9;
           text-transform: uppercase; margin-top: 4px; }
.mc-sub { font-size: 12px; line-height: 16px; font-weight: 600; letter-spacing: 0.05em; color: rgba(255,255,255,0.45); }
.mc-venue { position: absolute; bottom: 0; left: 0; right: 0; display: flex; justify-content: center; padding-bottom: 12px;
            z-index: 9; font-size: 12px; line-height: 16px; font-weight: 600; letter-spacing: 0.1em;
            text-transform: uppercase; color: rgba(255,255,255,0.25); }

@media (max-width: 720px) {
  .mc { height: 290px; }
  .mc-center { justify-content: flex-start; padding-top: 22px; }
  .mc-logo { width: 140px; height: 140px; }
  .mc-half.away .mc-logo-wrap { padding-left: 12px; }
  .mc-half.home .mc-logo-wrap { padding-right: 12px; }
  .mc-label { padding: 0 16px; }
  .mc-pct { font-size: 30px; }
  .mc-odds { gap: 24px; }
  .mc-name { font-size: 26px; }
  .mc-venue { display: none; }
}

/* ---------- "Calibrating…" bar ---------- */
.calib { display: none; margin-top: 16px; max-width: 420px; }
.calib-track { height: 6px; border-radius: 3px; background: #1f2b3d; border: 1px solid #2b3a4f; overflow: hidden; }
.calib-fill { height: 100%; width: 0; border-radius: 3px;
              background: linear-gradient(90deg, #2ecc8f, #7af0c4, #2ecc8f); background-size: 200% 100%;
              animation: calib-shimmer 1.1s linear infinite; }
.calib-label { margin-top: 8px; font-family: "Barlow Condensed", sans-serif; font-weight: 700; font-size: 0.9rem;
               letter-spacing: 0.14em; text-transform: uppercase; color: #93a3b8; }
@keyframes calib-shimmer { from { background-position: 200% 0; } to { background-position: 0 0; } }
@media (prefers-reduced-motion: reduce) { .calib-fill { animation: none; } }
```

### 6c. HTML placeholders

```html
<button id="predict-btn">Predict</button>

<div class="calib" id="calib" role="status" aria-live="polite">
  <div class="calib-track"><div class="calib-fill"></div></div>
  <div class="calib-label">Calibrating…</div>
</div>

<div class="mc" id="matchup-card" hidden></div>
```

### 6d. JavaScript

```js
const esc = s => String(s ?? "").replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const fmtPct = x => (x * 100).toFixed(1) + "%";

/** "2026-09-22" -> "Tue · Sep 22". The date is parsed as local time, so it
 *  doesn't shift by a day in timezones west of UTC. */
function fmtCardDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return `${dt.toLocaleDateString("en-US", { weekday: "short" })} · ${dt.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
}

function cardHalf(side, t) {
  return `
    <div class="mc-half ${side}">
      <div class="mc-glow"></div>
      <div class="mc-logo-wrap">
        <img class="mc-logo" src="${esc(t.logo)}" alt="${esc(t.city)} ${esc(t.nickname)} logo"
             onerror="this.style.visibility='hidden'">
      </div>
      <div class="mc-label">
        <span class="mc-city">${esc(t.city)}</span>
        <span class="mc-name">${esc(t.nickname)}</span>
        <span class="mc-abbr">${esc(t.code)}</span>
      </div>
    </div>`;
}

/**
 * Render the card. `away` / `home` are team objects (see §5).
 * opts: { date: "YYYY-MM-DD", pill?, sub?, venue? }
 */
function renderMatchupCard(el, away, home, opts = {}) {
  el.style.setProperty("--away-c", away.color);
  el.style.setProperty("--home-c", home.color);
  el.innerHTML = `
    <div class="mc-grain"></div>
    <div class="mc-divider"></div>
    ${cardHalf("away", away)}
    ${cardHalf("home", home)}
    <div class="mc-center">
      <div class="mc-pill">${esc(opts.pill ?? "Win probability")}</div>
      <div class="mc-odds">
        <span class="mc-pct away">—</span>
        <span class="mc-pct home">—</span>
      </div>
      ${opts.date ? `<span class="mc-date">${esc(fmtCardDate(opts.date))}</span>` : ""}
      ${opts.sub ? `<span class="mc-sub">${esc(opts.sub)}</span>` : ""}
    </div>
    <div class="mc-venue">${esc(opts.venue ?? home.venue ?? "")}</div>`;
}

function countUp(node, target, ms = 700) {
  const t0 = performance.now();
  const step = now => {
    const k = Math.min(1, (now - t0) / ms);
    node.textContent = fmtPct(target * (1 - Math.pow(1 - k, 3)));   // ease-out cubic
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/** Fill in the two percentages. probHome is between 0 and 1. */
function revealProbabilities(el, probHome) {
  const homeNode = el.querySelector(".mc-pct.home");
  const awayNode = el.querySelector(".mc-pct.away");
  countUp(homeNode, probHome);
  countUp(awayNode, 1 - probHome);
  (probHome >= 0.5 ? homeNode : awayNode).classList.add("fav");
}

/**
 * Show the "Calibrating…" bar while `work` (a Promise) runs, holding for at
 * least `minMs` so a fast response still reads as a deliberate beat instead
 * of a flicker. Resolves with work's value.
 */
async function withCalibration(calibEl, work, minMs = 1800) {
  const fill = calibEl.querySelector(".calib-fill");
  fill.style.transition = "none";
  fill.style.width = "0%";
  calibEl.style.display = "block";
  // Two animation frames: the browser needs to paint width:0 before the transition starts.
  requestAnimationFrame(() => requestAnimationFrame(() => {
    fill.style.transition = `width ${minMs}ms cubic-bezier(0.2, 0.7, 0.3, 1)`;
    fill.style.width = "88%";                                    // hold short of full until the work finishes
  }));
  try {
    const [value] = await Promise.all([work, sleep(minMs)]);
    fill.style.transition = "width 200ms ease-out";
    fill.style.width = "100%";
    await sleep(260);
    return value;
  } finally {
    calibEl.style.display = "none";
  }
}
```

### 6e. Wiring it together

```js
const TEAMS = {
  LAD: { code: "LAD", city: "Los Angeles", nickname: "Dodgers", color: "#005A9C",
         logo: "https://www.mlbstatic.com/team-logos/team-primary-on-dark/119.svg",
         venue: "Dodger Stadium · Los Angeles, CA" },
  CHC: { code: "CHC", city: "Chicago", nickname: "Cubs", color: "#0E3386",
         logo: "https://www.mlbstatic.com/team-logos/team-primary-on-dark/112.svg",
         venue: "Wrigley Field · Chicago, IL" },
};

document.getElementById("predict-btn").addEventListener("click", async () => {
  const card = document.getElementById("matchup-card");
  card.hidden = true;

  // Replace with your real call, e.g. fetch("/predict", {...}).then(r => r.json())
  const request = sleep(400).then(() => ({ probHome: 0.467 }));

  const { probHome } = await withCalibration(document.getElementById("calib"), request);
  renderMatchupCard(card, TEAMS.LAD, TEAMS.CHC, { date: "2026-09-22", sub: "Calibrated pregame model" });
  card.hidden = false;
  revealProbabilities(card, probHome);
});
```

If you want the card to show the matchup right away, before any result, call
`renderMatchupCard` whenever the team selection changes and only call
`revealProbabilities` once the result arrives. The percentages show "—"
until then.

## 7. Pitfalls I hit (and the fixes)

| Problem | Fix |
|---|---|
| Dark logos (navy, black) disappear on the card | Use the **on-dark** logo variants, not the default ones |
| Logos crowd the center or overlap each other | Put the mask on a **60%-wide wrapper** anchored to the outer edge, not on the `<img>` |
| Percentages placed in the team labels were unreadable over the logos | Move them to the **center**, one on each side of the divider |
| Team label colors copied straight from the template were nearly invisible (Boston navy on black) | Mix the team color with white (`color-mix(... 65%, white)`), keeping the glow in the true color |
| On a phone the center block collided with the bottom labels | Under 720px, top-align the center block, shrink the type, and hide the venue |
| Accented names came out garbled ("HernÃ¡ndez") | The data source sends UTF-8 without saying so. Decode the bytes as UTF-8 yourself (Python: `resp.content.decode("utf-8")`) |
| The progress bar jumped to its end with no animation | Set `width: 0`, wait **two** `requestAnimationFrame`s, then set the transition and target width |
| Date showed one day early | `new Date("2026-09-22")` is read as UTC midnight. Parse the parts into `new Date(y, m-1, d)` instead |
| Safari showed no fade | Add `-webkit-mask-image` alongside `mask-image` |

**Browser support:** `color-mix()` and `mask-image` work in all current
Chrome, Edge, Safari, and Firefox (2023+). For older browsers, precompute the
tints in JS, e.g. `hex + "55"` for 33% alpha.

## 8. Accessibility

- Logo `<img>`s carry `alt="{City} {Nickname} logo"`.
- The calibrating bar is `role="status" aria-live="polite"`, so screen
  readers announce "Calibrating…".
- The shimmer animation stops under `prefers-reduced-motion`. You can also
  set the minimum wait to about 300ms for those users.
- Contrast on the `#0a0a12` card: white labels are about 19:1, and the city
  label (55% white) is about 5.8:1, both above the 4.5:1 guideline for small
  text. The subtitle (45% white, about 4.1:1) and the pill text (50%) fall
  slightly short, so raise them to 55% if they carry essential information.
  The venue line (25%) is decorative only.

## 9. React + Tailwind port (sketch)

The original Figma Make version was React + Tailwind. The same structure as a
component:

```tsx
type Team = { code: string; city: string; nickname: string; color: string; logo: string; venue?: string };

export function MatchupCard({ away, home, date, probHome }: {
  away: Team; home: Team; date: string; probHome?: number;
}) {
  const style = { "--away-c": away.color, "--home-c": home.color } as React.CSSProperties;
  const fav = probHome === undefined ? null : probHome >= 0.5 ? "home" : "away";
  return (
    <div className="mc" style={style}>
      <div className="mc-grain" />
      <div className="mc-divider" />
      {(["away", "home"] as const).map(side => {
        const t = side === "away" ? away : home;
        return (
          <div key={side} className={`mc-half ${side}`}>
            <div className="mc-glow" />
            <div className="mc-logo-wrap"><img className="mc-logo" src={t.logo} alt={`${t.city} ${t.nickname} logo`} /></div>
            <div className="mc-label">
              <span className="mc-city">{t.city}</span>
              <span className="mc-name">{t.nickname}</span>
              <span className="mc-abbr">{t.code}</span>
            </div>
          </div>
        );
      })}
      <div className="mc-center">
        <div className="mc-pill">Win probability</div>
        <div className="mc-odds">
          <span className={`mc-pct away ${fav === "away" ? "fav" : ""}`}>{probHome === undefined ? "—" : `${((1 - probHome) * 100).toFixed(1)}%`}</span>
          <span className={`mc-pct home ${fav === "home" ? "fav" : ""}`}>{probHome === undefined ? "—" : `${(probHome * 100).toFixed(1)}%`}</span>
        </div>
        <span className="mc-date">{date}</span>
      </div>
      <div className="mc-venue">{home.venue}</div>
    </div>
  );
}
```

Reuse the CSS from §6b as a global stylesheet or CSS module; it doesn't need
Tailwind. For the count-up, animate a displayed value in a `useEffect` with
`requestAnimationFrame`. For the calibrating delay, `await
Promise.all([fetchResult(), sleep(1800)])` before setting `probHome`.

## 10. Adapting it

- **Different result:** change the pill text ("Projected score", "Series
  odds") and put any two values in `.mc-pct`, or remove `.mc-odds` for a pure
  matchup banner.
- **Not a prediction:** skip `withCalibration` and render the card directly,
  e.g. as a schedule header or a game-day hero image.
- **Lighter theme:** the fade relies on a dark background. On a light
  background, switch to the on-light logo variants, lower the glow to about
  15%, and make the text dark.
- **Wider or taller card:** the logo size and the 60% wrapper width set how
  much the logos overlap. Keep the logo at about 65% of the card height.
