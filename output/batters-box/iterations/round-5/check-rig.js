// Self-check for the swing rig: node check-rig.js <file containing rig:start…rig:end>
const fs = require("fs"), assert = require("assert");
const src = fs.readFileSync(process.argv[2] || __dirname + "/swing-rig.js", "utf8");
const rig = src.slice(src.indexOf("/* rig:start */"), src.indexOf("/* rig:end */"));
const { pose, project, swingTime, CONTACT, T0, SWING_END } = new Function(rig + "; return BatterRig;")();

const d = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
for (let t = T0; t <= SWING_END + 0.05; t += 0.002) {
  const q = pose(t);
  assert(q.strain < 0.005, `hands pulled off the bat at t=${t.toFixed(3)}`);
  assert(d(q.hipL, q.fF.ankle) <= 0.9005 && d(q.hipR, q.fB.ankle) <= 0.9005, `a leg can't reach its foot at t=${t.toFixed(3)}`);
  for (const k of ["head", "handL", "handR", "kneeL", "kneeR", "knob"]) assert(q[k].every(Number.isFinite), `${k} is not finite at t=${t}`);
  // everything stays inside the home diagram's viewBox (12 20 350 360)
  for (const p of [q.head, q.at(0.86), q.knob, q.fF.toe, q.fB.heel, q.handL]) {
    const [x, y] = project(p);
    assert(x > 12 && x < 362 && y > 20 && y < 380, `a point leaves the diagram at t=${t.toFixed(3)}: ${x.toFixed(0)},${y.toFixed(0)}`);
  }
}
assert(CONTACT.x > 216 && CONTACT.x < 336 && CONTACT.y > 152 && CONTACT.y < 266, `contact ${CONTACT.x},${CONTACT.y} is outside the zone`);
assert.strictEqual(swingTime(0, true), T0); assert.strictEqual(swingTime(0, false), T0);
assert(Math.abs(swingTime(900, true)) < 1e-9, "the fastball is not met at 900 ms");
assert(swingTime(900, false) > 0.05, "an off-speed pitch is not missed early");
for (const hit of [true, false]) for (let ms = 0; ms < 2000; ms += 5) assert(swingTime(ms + 5, hit) > swingTime(ms, hit), "the swing clock runs backwards");
console.log(`rig ok: contact (${CONTACT.x.toFixed(1)}, ${CONTACT.y.toFixed(1)}) scale ${CONTACT.scale.toFixed(2)}`);
