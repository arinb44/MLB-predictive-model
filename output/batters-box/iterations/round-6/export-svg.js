// Writes final/batters-box.svg from the shipped page: the home diagram with the rig's stance and
// the balls' seams drawn in, as the page shows them on load.   node export-svg.js
const fs = require("fs"), path = require("path"), assert = require("assert");
const ROOT = path.resolve(__dirname, "../../../..");
const html = fs.readFileSync(path.join(ROOT, "src/api/static/index.html"), "utf8");

// just enough DOM for the rig: elements that take attributes, children, and re-parenting
class El {
  constructor(tag) { this.tag = tag; this.attrs = {}; this.kids = []; this.parent = null; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  appendChild(c) { if (c.parent) c.parent.kids.splice(c.parent.kids.indexOf(c), 1); c.parent = this; this.kids.push(c); return c; }
  toString() {
    const a = Object.entries(this.attrs).map(([k, v]) => ` ${k}="${v}"`).join("");
    return this.kids.length ? `<${this.tag}${a}>${this.kids.join("")}</${this.tag}>` : `<${this.tag}${a}/>`;
  }
}
global.document = { createElementNS: (_, tag) => new El(tag) };

const between = (s, a, b) => { const i = s.indexOf(a); assert(i >= 0, `not found: ${a}`); return s.slice(i, s.indexOf(b, i)); };
const BatterRig = new Function(between(html, "const BatterRig", "// the barrel meets") + "; return BatterRig;")();
const { drawSeam, SPIN } = new Function(between(html, "const SPIN = {", "document.querySelectorAll(\".ball\").forEach(g => drawSeam") + "; return { drawSeam, SPIN };")();

const batter = new El("g"); batter.setAttribute("class", "batter");
BatterRig.makeRig(batter)(BatterRig.T0);
const C = BatterRig.CONTACT;

let svg = between(html, '<svg viewBox="12 20 350 360"', "</svg>") + "</svg>";
svg = svg.replace('<g class="batter"></g>', String(batter))
         .replace('<g class="burst-at">', `<g class="burst-at" transform="translate(${C.x.toFixed(1)},${C.y.toFixed(1)})">`);
let n = 0;
svg = svg.replace(/(data-p="(\d)"[\s\S]*?)<path class="ball-seam"\/>/g, (_, pre, p) => {
  const seam = new El("path"); seam.setAttribute("class", "ball-seam"); drawSeam(seam, SPIN[p][0], 0); n++;
  return pre + seam;
});
assert.strictEqual(n, 6, "expected six seams");
assert(!svg.includes('<g class="batter"></g>'), "the batter was not drawn");

fs.writeFileSync(path.join(ROOT, "output/batters-box/final/batters-box.svg"), `<?xml version="1.0" encoding="UTF-8"?>
<!-- Full Count - the batter's box, as the home page draws it on load (exported from
     src/api/static/index.html by iterations/round-6/export-svg.js).
     Umpire's view. The batter is BatterRig's stance: a 3D skeleton projected from the umpire's
     eye, each part a solid tone of chalk mixed into the ground. On a pitch the page redraws
     him every frame through the swing. .burst-at sits on the rig's contact point; each ball is
     a chalk body with its seams drawn where they face us, redrawn as it spins, and carries a
     .call-out that reads Strike on a miss. Balls are hidden until thrown. Colours come from the
     page CSS. -->
${svg}
`);
console.log(`wrote final/batters-box.svg (${svg.length} chars, 6 seams)`);
