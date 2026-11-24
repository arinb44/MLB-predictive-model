"""M7 round 5: swap the five-layer CSS swing in index.html for the swing rig.

    python3 build.py                       # writes iterations/round-5/index.html (the candidate)
    python3 build.py <path>                # writes there instead; M7c uses src/api/static/index.html

Reads src/api/static/index.html, runs check-rig.js first, and refuses to write if
any edit no longer finds its target (so it cannot run twice on the same file).
"""
import pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / "src/api/static/index.html"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "index.html"

subprocess.run(["node", str(HERE / "check-rig.js")], check=True)
rig_js = (HERE / "swing-rig.js").read_text()
rig = rig_js[rig_js.index("/* rig:start */") + len("/* rig:start */"):rig_js.index("/* rig:end */")].strip()

html = SRC.read_text()
before = len(html.splitlines())


def swap(old, new, regex=False):
    global html
    if regex:
        html, n = re.subn(old, lambda _: new, html, count=1, flags=re.S)
    else:
        n = html.count(old)
        html = html.replace(old, new, 1)
    if n != 1:
        sys.exit(f"build.py: target not found exactly once: {old[:70]!r}")


# ---- CSS: the old rig's rules out, the new rig's in
swap("  .b-dim { opacity: .62; }          /* one opacity per mass, so overlaps show no seam */\n"
     "  .b-fill { fill: var(--chalk); }\n", "")
swap(r"  \.bat-trail \{.*?\n  \.b-body  \{[^\n]*\n",
     "  /* the batter: each part takes a solid --tone, chalk mixed into the ground,\n"
     "     so overlapping parts cover each other instead of brightening */\n"
     "  .r-limb  { fill: none; stroke: var(--tone, var(--chalk)); stroke-linecap: round; stroke-linejoin: round; }\n"
     "  .r-solid { fill: var(--tone, var(--chalk)); stroke: var(--tone, var(--chalk)); stroke-linejoin: round; }\n"
     "  .r-handle { fill: var(--chalk); opacity: .85; }\n"
     "  .r-barrel, .r-trail { fill: var(--accent); }\n"
     "  .r-belt { fill: none; stroke: var(--ground); stroke-linecap: round; }\n", regex=True)

# ---- markup: the hand-drawn figure becomes an empty group the rig draws into
burst = re.search(r'<g class="contact-burst"[^>]*>(.*?</g><circle class="burst-core" r="6.5"/>)</g>', html).group(1)
swap(r"          <!-- batter: a filled silhouette.*?(?=          <!-- home plate)",
     "          <!-- batter: drawn on load by BatterRig, a 3D skeleton seen from the\n"
     "               umpire's eye, and swung when a pitch is thrown -->\n"
     '          <g class="batter"></g>\n'
     "          <!-- contact burst; script moves it onto the rig's contact point -->\n"
     f'          <g class="burst-at"><g class="contact-burst">{burst}</g></g>\n\n', regex=True)

# ---- showTab puts him back in his stance whenever the view changes
swap('  document.querySelectorAll(".ball").forEach(b => b.getAnimations().forEach(a => a.cancel()));\n',
     '  document.querySelectorAll(".ball").forEach(b => b.getAnimations().forEach(a => a.cancel()));\n'
     "  resetBatter();   // and the batter back in his stance\n")

# ---- JS: the rig, its loop, and playPitch without the WAAPI swing
swap(r"const TRAVEL_MS = 900, SWING_TOTAL = 900, FLIGHT_MS = 520;.*?(?=function ballRest)",
     "const TRAVEL_MS = 900, FLIGHT_MS = 520;\n"
     "// a beat after the pitch finishes, so the contact lands before the page moves\n"
     "const HOLD_MS = 1000;\n\n"
     + rig + "\n\n"
     "// the barrel meets the fastball wherever the rig's sweet spot is at contact:\n"
     "// out in front of the plate, so a touch farther away and smaller\n"
     "const CONTACT_POINT = BatterRig.CONTACT;\n"
     "let swingRun = 0;\n"
     "// var, not const: showTab can run before this line, and resetBatter checks it\n"
     'var drawBatter = document.querySelector(".batter") ? BatterRig.makeRig(document.querySelector(".batter")) : null;\n'
     "if (drawBatter) drawBatter(BatterRig.T0);\n"
     'document.querySelector(".burst-at")?.setAttribute("transform", `translate(${CONTACT_POINT.x.toFixed(1)},${CONTACT_POINT.y.toFixed(1)})`);\n\n'
     "// one swing at a time, on its own clock from the release; he holds the finish\n"
     "function swingBatter(hit) {\n"
     "  if (!drawBatter) return;\n"
     "  const run = ++swingRun, start = performance.now();\n"
     "  const step = now => {\n"
     "    if (run !== swingRun) return;\n"
     "    const t = BatterRig.swingTime(now - start, hit);\n"
     "    drawBatter(t);\n"
     "    if (t < BatterRig.SWING_END) requestAnimationFrame(step);\n"
     "  };\n"
     "  requestAnimationFrame(step);\n"
     "}\n"
     "function resetBatter() {\n"
     "  if (!drawBatter) return;\n"
     "  swingRun++;\n"
     "  drawBatter(BatterRig.T0);\n"
     "}\n\n", regex=True)

swap(r"  const swing = document\.querySelector\(\"\.b-swing\"\);.*?return Promise\.resolve\(\);\n",
     '  const burst = document.querySelector(".contact-burst");\n'
     "  if (!g || !burst || reduceMotion.matches) return Promise.resolve();\n", regex=True)
swap("  const land = hit ? CONTACT_POINT : rest;\n",
     "  const land = hit ? CONTACT_POINT : { ...rest, scale: 1 };\n")
swap("    { transform: `translate(${land.x}px, ${land.y}px) scale(1)`, opacity: 1 },\n"
     "  ], { duration: TRAVEL_MS,",
     "    { transform: `translate(${land.x}px, ${land.y}px) scale(${land.scale})`, opacity: 1 },\n"
     "  ], { duration: TRAVEL_MS,")
swap(r"  // the fastball is timed so the barrel arrives with the ball;.*?\}, Math\.max\(0, swingAt\)\);\n",
     "  // the same swing on every pitch, timed for the fastball, so anything\n"
     "  // slower finds him already through the zone: how you actually miss one\n"
     "  swingBatter(hit);\n", regex=True)
swap("      { transform: `translate(${land.x}px, ${land.y}px) scale(1)`, opacity: 1 },\n"
     '      { transform: "translate(470px, 40px) scale(0.18)", opacity: 0 },',
     "      { transform: `translate(${land.x}px, ${land.y}px) scale(${land.scale})`, opacity: 1 },\n"
     '      { transform: "translate(470px, 40px) scale(0.18)", opacity: 0 },')

for gone in ("b-swing", "b-arc", "b-reach", "bat-trail", "arm-back", "SWING_TOTAL", "CONTACT_FRAC"):
    assert gone not in html, f"build.py: {gone} is still in the page"
OUT.write_text(html)
print(f"wrote {OUT} ({len(html.splitlines())} lines, was {before})")
