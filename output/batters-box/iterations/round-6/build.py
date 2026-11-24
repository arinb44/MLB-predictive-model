"""M7 round 6: round 5's swing, plus spinning balls with no numbers and no dotted outline.

    python3 build.py                       # writes iterations/round-6/index.html (the candidate)
    python3 build.py <path>                # writes there instead; M7c uses src/api/static/index.html

Runs round 5's build.py into the same path first, then edits the balls in place.
"""
import pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "index.html"
subprocess.run([sys.executable, str(HERE.parent / "round-5" / "build.py"), str(OUT)], check=True)
html = OUT.read_text()


def swap(old, new, regex=False, count=1):
    global html
    if regex:
        html, n = re.subn(old, lambda m: m.expand(new) if "\\" in new else new, html, flags=re.S)
    else:
        n = html.count(old)
        html = html.replace(old, new)
    if n != count:
        sys.exit(f"round-6 build.py: expected {count} of {old[:60]!r}, found {n}")


# ---- CSS: a solid ball with red seams instead of a dotted ring with a number
swap("  .mark-dot { fill: none; stroke: var(--chalk); stroke-width: 2; stroke-dasharray: 3 4.5; stroke-linecap: round; }\n"
     "  .mark-num { fill: var(--chalk); font-family: var(--display); font-weight: 700; font-size: 17px; text-anchor: middle; font-variant-numeric: tabular-nums; transition: fill .18s; }\n"
     "  .mark-seam { fill: none; stroke: var(--accent); stroke-width: 1.6; opacity: .85; }\n",
     "  /* a thrown ball: solid chalk, its seams redrawn each frame as it spins */\n"
     "  .ball-body { fill: var(--chalk); }\n"
     "  .ball-seam { fill: none; stroke: var(--accent); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }\n")
swap("  .ball:focus-visible { outline: none; }\n"
     "  .ball:focus-visible .mark-dot { stroke: var(--accent); stroke-width: 3; }\n", "")   # balls aren't focusable

# ---- markup: each ball is a body and one seam path
swap(r'<circle class="mark-dot" r="16"/>\s*<path class="mark-seam"[^>]*/>\s*<path class="mark-seam"[^>]*/>\s*<text class="mark-num" y="6">\d</text>',
     '<circle class="ball-body" r="16"/>\n            <path class="ball-seam"/>', regex=True, count=6)

# ---- the diagram's label no longer promises numbers
swap("with six numbered pitches:", "with six pitches:")

# ---- JS: spin, with each pitch's real spin axis
swap("function ballRest(g) {",
     "/* The seams are the real curve on a sphere, turned about each pitch's spin axis\n"
     "   (catcher's view: x toward first base, y up, z toward us) and drawn where they\n"
     "   face us. Relative rates are real; the spin itself is slowed further than the\n"
     "   flight, since 2,300 rpm at any frame rate is a blur. */\n"
     "const SPIN = {\n"
     "  1: [[-0.97, -0.24, 0], 2300],   // four-seam: backspin, a touch arm-side\n"
     "  2: [[0.35, 0.10, 0.93], 2450],  // slider: mostly gyro, the spinning dot\n"
     "  3: [[0.98, 0.20, 0], 2500],     // curveball: topspin\n"
     "  4: [[-0.80, -0.56, 0.20], 1750],// changeup: backspin tilted to the arm side\n"
     "  5: [[-0.60, -0.76, 0.25], 2150],// sinker: mostly sidespin\n"
     "  6: [[0.30, -0.30, 0.90], 2400], // cutter: gyro with a little backspin\n"
     "};\n"
     "const SPIN_TURNS = 2.2;           // turns a 2,300 rpm pitch makes on its way in\n"
     "const SEAM = Array.from({ length: 120 }, (_, i) => {\n"
     "  const t = i / 120 * 2 * Math.PI, a = 0.7, b = 0.3;   // a + b = 1 keeps it on the sphere\n"
     "  return [a * Math.cos(t) + b * Math.cos(3 * t), a * Math.sin(t) - b * Math.sin(3 * t), 2 * Math.sqrt(a * b) * Math.sin(2 * t)];\n"
     "});\n"
     "function drawSeam(path, axis, angle) {\n"
     "  const l = Math.hypot(...axis), [kx, ky, kz] = axis.map(v => v / l), c = Math.cos(angle), s = Math.sin(angle), r = 15;\n"
     "  let d = \"\", pen = false;\n"
     "  for (const [px, py, pz] of SEAM.concat([SEAM[0]])) {\n"
     "    const k = (kx * px + ky * py + kz * pz) * (1 - c);       // Rodrigues' rotation\n"
     "    const x = px * c + (ky * pz - kz * py) * s + kx * k;\n"
     "    const y = py * c + (kz * px - kx * pz) * s + ky * k;\n"
     "    const z = pz * c + (kx * py - ky * px) * s + kz * k;\n"
     "    if (z > 0) { d += `${pen ? \"L\" : \"M\"}${(x * r).toFixed(1)} ${(-y * r).toFixed(1)}`; pen = true; } else pen = false;\n"
     "  }\n"
     "  path.setAttribute(\"d\", d);\n"
     "}\n"
     "document.querySelectorAll(\".ball\").forEach(g => drawSeam(g.querySelector(\".ball-seam\"), SPIN[g.dataset.p][0], 0));\n"
     "function spinBall(g, n, ms) {\n"
     "  const seam = g.querySelector(\".ball-seam\"), [axis, rpm] = SPIN[n];\n"
     "  const rate = rpm / 2300 * SPIN_TURNS * 2 * Math.PI / TRAVEL_MS, start = performance.now();\n"
     "  const step = now => {\n"
     "    const e = Math.min(ms, now - start);\n"
     "    drawSeam(seam, axis, e * rate);\n"
     "    if (e < ms && g.classList.contains(\"thrown\")) requestAnimationFrame(step);   // a caught ball stops\n"
     "  };\n"
     "  requestAnimationFrame(step);\n"
     "}\n\n"
     "function ballRest(g) {")
swap("  swingBatter(hit);\n",
     "  swingBatter(hit);\n"
     "  spinBall(g, n, hit ? TRAVEL_MS + FLIGHT_MS : TRAVEL_MS);\n")

for gone in ("mark-dot", "mark-num", "mark-seam", "stroke-dasharray: 3 4.5"):
    assert gone not in html, f"round-6 build.py: {gone} is still in the page"
OUT.write_text(html)
print(f"round 6 applied to {OUT}")
