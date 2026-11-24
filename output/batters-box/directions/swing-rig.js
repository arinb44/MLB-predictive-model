/* Full Count, M7: a realistic swing.
   A 3D skeleton keyed to the phases of a real swing, projected from the
   umpire's position the home diagram is drawn from. Everything above
   "review page" is the rig that would merge into index.html; the rest is
   the review harness for the direction pages and never ships. */
"use strict";

/* ================= scene ================= */
// metres; x toward the plate, y up, z toward the camera (the pitcher is at -z)
const CAM = { x: 0, y: 1.35, z: 6.0 }, FOCAL = 918, OX = 276, OY = 121.5;
function project(p) {
  const s = FOCAL / (CAM.z - p[2]);
  return [OX + s * (p[0] - CAM.x), OY - s * (p[1] - CAM.y), s];
}
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const len = a => Math.hypot(a[0], a[1], a[2]);
const unit = a => mul(a, 1 / (len(a) || 1));
const lerp3 = (a, b, k) => add(a, mul(sub(b, a), k));
const UP = [0, 1, 0];
const rad = d => d * Math.PI / 180;
// yaw 0 faces the plate (+x); +90 faces the pitcher (-z)
const heading = deg => [Math.cos(rad(deg)), 0, -Math.sin(rad(deg))];
// the body's right-hand side at that yaw (toward the camera at 0)
const rightOf = deg => [Math.sin(rad(deg)), 0, Math.cos(rad(deg))];
const perpTo = (v, n) => unit(sub(v, mul(n, dot(v, n))));

/* ================= the swing =================
   Real seconds, contact at 0. A right-handed hitter facing the plate.
   p* pelvis, t* torso (yaw, forward lean, side tilt toward the back side),
   h* the grip, az/el the bat's direction, f* front foot, b* back foot
   (yaw of the toes, heel lift in degrees). Hips lead the shoulders, the
   shoulders lead the hands, the barrel comes last. */
const SWING = [
  { t: -0.43,  name: "Stance",    px: -1.05, py: 0.90, pz:  0.00, pyaw:  -5, tyaw: -15, lean: 22, tilt:  0, hx: -0.78, hy: 1.40, hz:  0.20, az: -160, el:  40, fz: -0.34, fl: 0,    fyaw: 15, fh:  0, bz: 0.32, byaw:  5, bh:  0 },
  { t: -0.27,  name: "Load",      px: -1.06, py: 0.89, pz:  0.05, pyaw: -18, tyaw: -32, lean: 22, tilt: -3, hx: -0.84, hy: 1.45, hz:  0.3, az: -166, el:  44, fz: -0.37, fl: 0.1, fyaw:  5, fh: 12, bz: 0.32, byaw:  5, bh:  0 },
  { t: -0.16,  name: "Plant",     px: -1.05, py: 0.87, pz: -0.07, pyaw:  -6, tyaw: -28, lean: 23, tilt:  5, hx: -0.84, hy: 1.40, hz:  0.25, az: -160, el:  38, fz: -0.60, fl: 0,    fyaw: 25, fh:  0, bz: 0.32, byaw:  8, bh:  6 },
  { t: -0.075, name: "Slot",      px: -1.00, py: 0.86, pz: -0.11, pyaw:  30, tyaw:   5, lean: 22, tilt: 20, hx: -0.78, hy: 1.15, hz:  0.10, az:  -118, el:  8, fz: -0.60, fl: 0,    fyaw: 35, fh:  0, bz: 0.32, byaw: 25, bh: 22 },
  { t:  0,     name: "Contact",   px: -0.98, py: 0.89, pz: -0.13, pyaw:  55, tyaw:  40, lean: 22, tilt: 28, hx: -0.50, hy: 0.94, hz: -0.30, az:   28, el: -25, fz: -0.60, fl: 0,    fyaw: 45, fh:  0, bz: 0.30, byaw: 50, bh: 45 },
  { t:  0.05,  name: "Extension", px: -0.98, py: 0.9, pz: -0.14, pyaw:  70, tyaw:  75, lean: 18, tilt: 24, hx: -0.55, hy: 1.03, hz: -0.50, az:   85, el:  -5, fz: -0.60, fl: 0,    fyaw: 45, fh:  0, bz: 0.29, byaw: 65, bh: 55 },
  { t:  0.12,  name: "Rollover",  px: -0.98, py: 0.88, pz: -0.14, pyaw:  82, tyaw: 105, lean: 15, tilt: 14, hx: -0.82, hy: 1.30, hz: -0.50, az:  170, el:  20, fz: -0.60, fl: 0,    fyaw: 45, fh:  0, bz: 0.28, byaw: 75, bh: 60 },
  { t:  0.26,  name: "Finish",    px: -0.98, py: 0.90, pz: -0.14, pyaw:  88, tyaw: 125, lean: 10, tilt:  5, hx: -1.22, hy: 1.55, hz: -0.32, az:  255, el: -35, fz: -0.60, fl: 0,    fyaw: 45, fh:  0, bz: 0.28, byaw: 85, bh: 65 },
];
const BODY = { hip: 0.09, thigh: 0.45, shin: 0.45, ankle: 0.08, spine: 0.50, shoulder: 0.19,
               upper: 0.29, fore: 0.32, bat: 0.86, grip: 0.06, hands: 0.045 };
const FOOT_X = -0.87;                     // ball of the foot; the ankle sits under the hip
const SWEET = 0.70;                       // contact spot, from the knob
const T0 = SWING[0].t;                    // the click: ball release on the fastball
const EARLY = 0.08;                       // off-speed: the same swing, this much early
const SLOW = 900 / 430;                   // approved: slow motion, true proportions

// monotone cubic per channel, so holds stay still and nothing overshoots
const TIMES = SWING.map(k => k.t);
const CHANNELS = Object.keys(SWING[0]).filter(k => k !== "t" && k !== "name");
const TANGENTS = {};
for (const c of CHANNELS) {
  const p = SWING.map(k => k[c]), n = p.length, d = [], m = new Array(n).fill(0);
  for (let i = 0; i < n - 1; i++) d[i] = (p[i + 1] - p[i]) / (TIMES[i + 1] - TIMES[i]);
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) { m[i] = m[i + 1] = 0; continue; }
    const a = m[i] / d[i], b = m[i + 1] / d[i], h = a * a + b * b;
    if (h > 9) { const s = 3 / Math.sqrt(h); m[i] = s * a * d[i]; m[i + 1] = s * b * d[i]; }
  }
  TANGENTS[c] = m;
}
function channels(t) {
  const n = TIMES.length;
  if (t <= TIMES[0]) return SWING[0];
  if (t >= TIMES[n - 1]) return SWING[n - 1];
  let i = 0; while (t > TIMES[i + 1]) i++;
  const h = TIMES[i + 1] - TIMES[i], s = (t - TIMES[i]) / h, s2 = s * s, s3 = s2 * s;
  const a = 2 * s3 - 3 * s2 + 1, b = s3 - 2 * s2 + s, c = -2 * s3 + 3 * s2, d = s3 - s2;
  const out = {};
  for (const k of CHANNELS) out[k] = a * SWING[i][k] + b * h * TANGENTS[k][i] + c * SWING[i + 1][k] + d * h * TANGENTS[k][i + 1];
  return out;
}

// two-bone IK: the joint between root and target, bending toward the pole
function ik(root, target, l1, l2, pole) {
  const d = sub(target, root), dist = Math.max(Math.abs(l1 - l2) + 1e-3, Math.min(len(d), l1 + l2 - 1e-3));
  const dir = unit(d);
  const a = Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))));
  return add(root, add(mul(dir, l1 * Math.cos(a)), mul(perpTo(pole, dir), l1 * Math.sin(a))));
}
function foot(z, yaw, heel, lift) {
  const toeDir = heading(yaw), h = rad(heel);
  const ball = [FOOT_X, lift, z];
  const along = add(mul(toeDir, Math.cos(h)), mul(UP, -Math.sin(h)));       // heel → ball
  const normal = add(mul(UP, Math.cos(h)), mul(toeDir, Math.sin(h)));
  const heelPt = sub(ball, mul(along, 0.19));
  return { heel: heelPt, ball, toe: add(ball, mul(toeDir, 0.07)),
           ankle: add(add(heelPt, mul(along, 0.05)), mul(normal, BODY.ankle)) };
}
const RELEASE_3D = [0, 1.9, -17], LOOK_AT = [0.05, 0.7, -0.6];

function pose(t) {
  const c = channels(t);
  const P = [c.px, c.py, c.pz];
  const fp = heading(c.pyaw), rp = rightOf(c.pyaw), ft = heading(c.tyaw), rt = rightOf(c.tyaw);
  const cl = Math.cos(rad(c.lean));
  const spine = unit(add(add(mul(UP, cl * Math.cos(rad(c.tilt))), mul(ft, Math.sin(rad(c.lean)))), mul(rt, Math.sin(rad(c.tilt)) * cl)));
  const N = add(P, mul(spine, BODY.spine));
  const across = perpTo(rt, spine), chest = perpTo(ft, spine);
  const shL = sub(N, mul(across, BODY.shoulder)), shR = add(N, mul(across, BODY.shoulder));
  const hipL = sub(P, mul(rp, BODY.hip)), hipR = add(P, mul(rp, BODY.hip));
  const head = add(N, add(mul(spine, 0.05), mul(UP, 0.15)));
  // the eyes ride the ball in from the release point to the contact point
  const k = Math.max(0, Math.min(1, (t - T0) / -T0));
  const look = unit(sub(lerp3(RELEASE_3D, LOOK_AT, k * k), head));

  const u = [Math.cos(rad(c.el)) * Math.cos(rad(c.az)), Math.sin(rad(c.el)), -Math.cos(rad(c.el)) * Math.sin(rad(c.az))];
  // both hands stay on the handle: pull the grip in if either arm can't reach
  let G = [c.hx, c.hy, c.hz], strain = 0;
  const reach = BODY.upper + BODY.fore - 0.005;
  for (let i = 0; i < 4; i++) for (const [sh, off] of [[shL, -BODY.hands], [shR, BODY.hands]]) {
    const d = sub(add(G, mul(u, off)), sh), L = len(d);
    if (L > reach) { G = sub(G, mul(unit(d), L - reach)); strain += L - reach; }
  }
  const handL = add(G, mul(u, -BODY.hands)), handR = add(G, mul(u, BODY.hands));
  const elbL = ik(shL, handL, BODY.upper, BODY.fore, add(mul(UP, -1), add(mul(across, -0.5), mul(chest, 0.2))));
  const elbR = ik(shR, handR, BODY.upper, BODY.fore, add(mul(UP, -1), add(mul(across, 0.6), mul(chest, -0.1))));
  const fF = foot(c.fz, c.fyaw, c.fh, c.fl), fB = foot(c.bz, c.byaw, c.bh, 0);
  const kneeL = ik(hipL, fF.ankle, BODY.thigh, BODY.shin, add(heading(c.fyaw), mul(fp, 0.6)));
  const kneeR = ik(hipR, fB.ankle, BODY.thigh, BODY.shin, add(heading(c.byaw), mul(fp, 0.6)));
  const knob = sub(G, mul(u, BODY.grip));
  return { t, P, N, spine, across, chest, fp, rp, shL, shR, hipL, hipR, head, look, u, G, knob,
           handL, handR, elbL, elbR, kneeL, kneeR, fF, fB, strain,
           at: d => add(knob, mul(u, d)) };
}
// where the barrel meets the fastball: the sweet spot at contact, on screen
const CONTACT = (() => { const p = project(pose(0).at(SWEET)); return { x: p[0], y: p[1], scale: p[2] / (FOCAL / CAM.z) }; })();

// the batter's clock for a pitch: a fooled hitter runs the same swing, sooner
function swingTime(ms, hit) {
  const real = ms / 1000 / SLOW, k = hit ? 1 : -T0 / (-T0 - EARLY), pre = -T0 / k;
  return real < pre ? T0 + real * k : real - pre;
}

/* ================= drawing ================= */
const NS = "http://www.w3.org/2000/svg";
function el(tag, cls, parent, attrs) {
  const e = document.createElementNS(NS, tag);
  if (cls) e.setAttribute("class", cls);
  if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
  parent.appendChild(e);
  return e;
}
const f1 = n => n.toFixed(1);
function seg(path, a, b, w) {
  const p = project(a), q = project(b);
  path.setAttribute("d", `M${f1(p[0])} ${f1(p[1])}L${f1(q[0])} ${f1(q[1])}`);
  path.setAttribute("stroke-width", f1(w * (p[2] + q[2]) / 2));
}
function poly(path, pts, w) {
  const pr = pts.map(project);
  path.setAttribute("d", "M" + pr.map(p => `${f1(p[0])} ${f1(p[1])}`).join("L"));
  path.setAttribute("stroke-width", f1(w * pr.reduce((s, p) => s + p[2], 0) / pr.length));
}
function disc(circle, c, r) {
  const p = project(c);
  circle.setAttribute("cx", f1(p[0])); circle.setAttribute("cy", f1(p[1])); circle.setAttribute("r", f1(r * p[2]));
}
function hull(path, pts, w) {
  const pr = pts.map(project).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const x = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], hi = [];
  for (const p of pr) { while (lo.length > 1 && x(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
  for (let i = pr.length - 1; i >= 0; i--) { const p = pr[i]; while (hi.length > 1 && x(hi[hi.length - 2], hi[hi.length - 1], p) <= 0) hi.pop(); hi.push(p); }
  const h = lo.slice(0, -1).concat(hi.slice(0, -1));
  path.setAttribute("d", "M" + h.map(p => `${f1(p[0])} ${f1(p[1])}`).join("L") + "Z");
  path.setAttribute("stroke-width", f1(w * pr[0][2]));
}
// a tapered solid along the bat: [distance from knob, radius] pairs
function taper(path, q, profile) {
  const a = project(q.knob), b = project(q.at(BODY.bat));
  let nx = -(b[1] - a[1]), ny = b[0] - a[0];
  const nl = Math.hypot(nx, ny) || 1; nx /= nl; ny /= nl;
  const L = [], R = [];
  for (const [d, r] of profile) {
    const p = project(q.at(d)), w = r * p[2];
    L.push(`${f1(p[0] + nx * w)} ${f1(p[1] + ny * w)}`);
    R.unshift(`${f1(p[0] - nx * w)} ${f1(p[1] - ny * w)}`);
  }
  path.setAttribute("d", "M" + L.concat(R).join("L") + "Z");
}
const HANDLE = [[0, 0.012], [0.30, 0.013], [0.47, 0.018]];
const BARREL = [[0.46, 0.018], [0.62, 0.033], [BODY.bat, 0.033]];

function ring(out, c, across, front, a, b) {
  for (let i = 0; i < 10; i++) { const th = i * Math.PI / 5; out.push(add(c, add(mul(across, a * Math.cos(th)), mul(front, b * Math.sin(th))))); }
}
function torsoPoints(q, top, bottom) {
  // stacked elliptical sections, shoulders to seat; the hull of them is the outline
  const pts = [], at = k => lerp3(q.P, q.N, k);
  if (top) { ring(pts, sub(q.N, mul(q.spine, 0.05)), q.across, q.chest, 0.21, 0.10); ring(pts, at(0.72), q.across, q.chest, 0.18, 0.13); }
  ring(pts, at(0.32), q.across, q.chest, 0.15, 0.11);
  if (bottom) { ring(pts, q.P, q.rp, q.fp, 0.17, 0.12); ring(pts, add(q.P, add(mul(UP, -0.08), mul(q.fp, -0.03))), q.rp, q.fp, 0.14, 0.11); }
  return pts;
}

/* makeRig(parent, style): style is "chalk" (A), "strobe" (B) or "uniform" (C).
   Returns draw(t) for a time in real seconds, contact at 0. */
function makeRig(parent, style) {
  const root = el("g", "rig", parent);
  const uniform = style === "uniform";
  const body = el("g", uniform ? null : "b-dim", root);
  // C: solid tones mixed from chalk into the ground, so overlapping parts cover
  // each other instead of brightening where they cross
  const tone = pct => ({ style: `--tone: color-mix(in srgb, var(--chalk) ${pct}%, var(--ground))` });
  const layer = pct => uniform ? el("g", null, body, tone(pct)) : body;
  const shoes = layer(30), socks = layer(40), pants = layer(56), jersey = layer(72), helmet = layer(46);
  const parts = {
    legL: [el("path", "r-limb", pants), el("path", "r-limb", socks), el("path", "r-limb", shoes)],
    legR: [el("path", "r-limb", pants), el("path", "r-limb", socks), el("path", "r-limb", shoes)],
    hips: el("path", "r-solid", pants),
    torso: el("path", "r-solid", jersey),
    neck: el("path", "r-limb", jersey),
    head: el("circle", "r-solid", helmet),
    brim: el("path", "r-limb", helmet),
  };
  const belt = uniform ? el("path", "r-belt", body) : null;
  const arm = () => { const g = el("g", null, root, uniform ? tone(82) : { opacity: 0.62 }); return { g, up: el("path", "r-limb", g), lo: el("path", "r-limb", g) }; };
  const armL = arm(), armR = arm();
  const fx = el("g", null, root);   // trail or strobe, sorted with the bat
  const bat = el("g", null, root);
  const hands = [el("circle", "r-solid" + (uniform ? "" : " b-dim"), bat), el("circle", "r-solid" + (uniform ? "" : " b-dim"), bat)];
  const knob = el("circle", "r-handle", bat), handle = el("path", "r-handle", bat);
  const barrel = el("path", "r-barrel", bat), cap = el("circle", "r-barrel", bat);

  // A and C: a short ribbon behind the barrel along the path it really took
  const RIB = 12, RIB_DT = 0.008;
  const ribbon = style === "strobe" ? [] : Array.from({ length: RIB }, () => el("path", "r-trail", fx));
  // B: ghost bats stamped through the swing, like a chronophotograph
  const GHOST_T = [-0.075, -0.05, -0.03, -0.015, 0, 0.015, 0.03, 0.05, 0.08, 0.12];
  const ghosts = style !== "strobe" ? [] : GHOST_T.map(gt => {
    const g = el("g", null, fx), q = pose(gt);
    taper(el("path", "r-handle", g), q, HANDLE);
    taper(el("path", "r-barrel", g), q, BARREL);
    disc(el("circle", "r-barrel", g), q.at(BODY.bat), 0.033);
    return { g, t: gt };
  });

  let order = "";
  return function draw(t) {
    const q = pose(t);
    // legs: thigh in the pants, shin in the socks, foot in the shoe
    for (const [p, hip, knee, f] of [[parts.legL, q.hipL, q.kneeL, q.fF], [parts.legR, q.hipR, q.kneeR, q.fB]]) {
      seg(p[0], hip, knee, 0.17);
      if (uniform) { const sock = lerp3(knee, f.ankle, 0.25); seg(p[1], knee, f.ankle, 0.12); seg(p[0], hip, sock, 0.17); }
      else seg(p[1], knee, f.ankle, 0.12);
      poly(p[2], [f.heel, f.ball, f.toe], 0.09);
    }
    if (uniform) { hull(parts.torso, torsoPoints(q, true, false), 0.04); hull(parts.hips, torsoPoints(q, false, true), 0.04); }
    else { hull(parts.torso, torsoPoints(q, true, true), 0.04); parts.hips.setAttribute("d", ""); }
    if (belt) { const w = lerp3(q.P, q.N, 0.29); seg(belt, sub(w, mul(q.across, 0.17)), add(w, mul(q.across, 0.17)), 0.025); }
    seg(parts.neck, q.N, q.head, 0.11);
    disc(parts.head, q.head, uniform ? 0.135 : 0.125);
    seg(parts.brim, add(q.head, add(mul(q.look, 0.1), mul(UP, 0.035))), add(q.head, add(mul(q.look, uniform ? 0.2 : 0.18), mul(UP, 0.015))), 0.045);
    seg(armL.up, q.shL, q.elbL, 0.10); seg(armL.lo, q.elbL, q.handL, 0.085);
    seg(armR.up, q.shR, q.elbR, 0.10); seg(armR.lo, q.elbR, q.handR, 0.085);
    disc(hands[0], q.handL, 0.045); disc(hands[1], q.handR, 0.045);
    disc(knob, q.knob, 0.022);
    taper(handle, q, HANDLE); taper(barrel, q, BARREL); disc(cap, q.at(BODY.bat), 0.033);

    if (ribbon.length) {
      let prev = null;
      for (let i = 0; i <= RIB; i++) {
        const ti = t - i * RIB_DT, on = ti >= -0.09 && ti <= 0.16;   // fast part only: slot to rollover
        const r = pose(ti), a = project(r.at(0.5)), b = project(r.at(BODY.bat));
        if (i > 0) {
          const path = ribbon[i - 1];
          if (on && prev.on) {
            path.setAttribute("d", `M${f1(prev.a[0])} ${f1(prev.a[1])}L${f1(prev.b[0])} ${f1(prev.b[1])}L${f1(b[0])} ${f1(b[1])}L${f1(a[0])} ${f1(a[1])}Z`);
            path.setAttribute("opacity", (0.5 * (1 - (i - 1) / RIB)).toFixed(2));
          } else path.setAttribute("d", "");
        }
        prev = { a, b, on };
      }
    }
    for (const g of ghosts) {
      const age = t - 0.32;   // the strobe hangs through the finish, then fades
      const o = t < g.t ? 0 : (0.16 + 0.26 * (GHOST_T.indexOf(g.t) + 1) / GHOST_T.length) * Math.max(0, Math.min(1, 1 - age / 0.25));
      g.g.setAttribute("opacity", o.toFixed(2));
    }

    // painter's order: far parts first, re-sorted only when it changes
    const z = (...ps) => ps.reduce((s, p) => s + p[2], 0) / ps.length;
    const items = [[body, q.P[2]], [armL.g, z(q.shL, q.elbL, q.handL)], [armR.g, z(q.shR, q.elbR, q.handR)],
                   [bat, q.at(0.45)[2]], [fx, q.at(0.45)[2] - 0.001]].sort((a, b) => a[1] - b[1]);
    const key = items.map(i => [body, armL.g, armR.g, bat, fx].indexOf(i[0])).join("");
    if (key !== order) { order = key; for (const [g] of items) root.appendChild(g); }
    return q;
  };
}

/* ================= review page (never ships) ================= */
const PITCHES = [
  { n: 1, kind: "Fastball", x: 276, y: 209 }, { n: 2, kind: "Slider", x: 334, y: 250 },
  { n: 3, kind: "Curveball", x: 248, y: 171 }, { n: 4, kind: "Changeup", x: 288, y: 300 },
  { n: 5, kind: "Sinker", x: 236, y: 247 }, { n: 6, kind: "Cutter", x: 194, y: 176 },
];
const RELEASE = { x: 276, y: 196, scale: 0.12 };
const TRAVEL_MS = 900, FLIGHT_MS = 520, END_MS = 1900;
const OLD_CONTACT = { x: 264, y: 239, scale: 1 };

function bezier(x1, y1, x2, y2) {
  const B = (a, b, t) => 3 * a * (1 - t) * (1 - t) * t + 3 * b * (1 - t) * t * t + t * t * t;
  return x => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    let lo = 0, hi = 1, t = x;
    for (let i = 0; i < 30; i++) { t = (lo + hi) / 2; if (B(x1, x2, t) < x) lo = t; else hi = t; }
    return B(y1, y2, t);
  };
}
const easeTravel = bezier(0.55, 0, 0.9, 0.6), easeFlight = bezier(0.2, 0.6, 0.4, 1);
const easeCall = bezier(0.2, 0.7, 0.3, 1), easeBurst = bezier(0.2, 0.7, 0.4, 1);
function frames(list, p) {
  let i = 0; while (i < list.length - 2 && p > list[i + 1].o) i++;
  const a = list[i], b = list[i + 1], k = Math.max(0, Math.min(1, (p - a.o) / (b.o - a.o))), out = {};
  for (const key in a) if (key !== "o") out[key] = a[key] + (b[key] - a[key]) * k;
  return out;
}
const CALL = [{ o: 0, y: 6, s: 0.7, a: 0 }, { o: 0.18, y: 0, s: 1.08, a: 1 }, { o: 0.3, y: -2, s: 1, a: 1 }, { o: 0.62, y: -10, s: 1, a: 1 }, { o: 1, y: -18, s: 0.98, a: 0 }];
const BURST = [{ o: 0, s: 0.25, r: 0, a: 0 }, { o: 0.3, s: 1.15, r: 14, a: 1 }, { o: 1, s: 1.5, r: 22, a: 0 }];

function drawDiagram(svg) {
  svg.innerHTML = `<path class="z-chalk" d="M36 326 L196 326 L214 372 L18 372 Z"/>
    <g class="batter-slot"></g>
    <path class="plate-shape" d="M238 350 L314 350 L314 359 L276 369 L238 359 Z"/>
    <g>${[152, 190, 228].map(y => [216, 256, 296].map(x => `<rect class="z-cell" x="${x}" y="${y}" width="40" height="38"/>`).join("")).join("")}
    <rect class="z-edge" x="216" y="152" width="120" height="114"/></g>`;
  return svg.querySelector(".batter-slot");
}
function mountBall(svg) {
  const g = el("g", null, svg, { opacity: 0 });
  g.innerHTML = `<circle class="mark-dot" r="16"/><path class="mark-seam" d="M-9 -11 Q-14 0 -9 11"/><path class="mark-seam" d="M9 -11 Q14 0 9 11"/><text class="mark-num" y="6"></text>`;
  const call = el("text", "call-out", svg, { opacity: 0 }); call.textContent = "Strike";
  const burst = el("g", null, svg, { opacity: 0 });
  burst.innerHTML = `<g class="burst-rays"><polygon points="7.0,2.6 25.0,0.0 7.0,-2.6"/><polygon points="3.1,6.8 17.7,17.7 6.8,3.1"/><polygon points="-2.6,7.0 0.0,25.0 2.6,7.0"/><polygon points="-6.8,3.1 -17.7,17.7 -3.1,6.8"/><polygon points="-7.0,-2.6 -25.0,0.0 -7.0,2.6"/><polygon points="-3.1,-6.8 -17.7,-17.7 -6.8,-3.1"/><polygon points="2.6,-7.0 -0.0,-25.0 -2.6,-7.0"/><polygon points="6.8,-3.1 17.7,-17.7 3.1,-6.8"/></g><circle class="burst-core" r="6.5"/>`;
  return (ms, pitch, contact) => {
    const hit = pitch.n === 1, land = hit ? contact : { x: pitch.x, y: pitch.y, scale: 1 };
    g.querySelector("text").textContent = pitch.n;
    let x, y, s, a = 0;
    if (ms >= 0 && ms <= TRAVEL_MS) {
      const p = easeTravel(ms / TRAVEL_MS);
      x = RELEASE.x + (land.x - RELEASE.x) * p; y = RELEASE.y + (land.y - RELEASE.y) * p;
      s = RELEASE.scale + (land.scale - RELEASE.scale) * p; a = 0.35 + 0.65 * p;
    } else if (hit && ms > TRAVEL_MS && ms < TRAVEL_MS + FLIGHT_MS) {
      const p = easeFlight((ms - TRAVEL_MS) / FLIGHT_MS);
      x = land.x + (470 - land.x) * p; y = land.y + (40 - land.y) * p; s = land.scale + (0.18 - land.scale) * p; a = 1 - p;
    } else if (!hit && ms > TRAVEL_MS) { x = land.x; y = land.y; s = 1; a = 1; }
    if (a > 0) g.setAttribute("transform", `translate(${f1(x)},${f1(y)}) scale(${s.toFixed(3)})`);
    g.setAttribute("opacity", a.toFixed(2));
    const pc = (ms - TRAVEL_MS) / 950;
    if (!hit && pc >= 0 && pc <= 1) {
      const f = frames(CALL, easeCall(pc));
      call.setAttribute("transform", `translate(${land.x},${land.y - 28 + f.y}) scale(${f.s.toFixed(3)})`);
      call.setAttribute("opacity", f.a.toFixed(2));
    } else call.setAttribute("opacity", 0);
    const pb = (ms - TRAVEL_MS) / 280;
    if (hit && pb >= 0 && pb <= 1) {
      const f = frames(BURST, easeBurst(pb));
      burst.setAttribute("transform", `translate(${f1(land.x)},${f1(land.y)}) scale(${f.s.toFixed(3)}) rotate(${f1(f.r)})`);
      burst.setAttribute("opacity", f.a.toFixed(2));
    } else burst.setAttribute("opacity", 0);
  };
}

// today's five-layer swing, verbatim from index.html, made scrubbable
const OLD_MARKUP = "<g class=\"batter\"><g class=\"b-body b-dim\"><path class=\"b-fill\" d=\"M100 74 C100 55 110 45 123 45 C137 45 147 56 147 74 C147 88 140 97 130 99 L114 99 C104 97 100 86 100 74 Z\"/><path class=\"b-fill\" d=\"M143 68 C152 67 162 70 164 75 C162 80 151 82 142 80 Z\"/><path class=\"b-fill\" d=\"M112 95 L134 95 L138 116 L110 116 Z\"/><path class=\"b-fill\" d=\"M100 116 C94 128 92 148 96 168 C98 182 100 192 102 202 L146 202 C148 190 151 176 153 160 C156 140 152 126 146 114 Z\"/><path class=\"b-stroke\" d=\"M133 200 L139 252\" stroke-width=\"26\"/><path class=\"b-stroke\" d=\"M139 252 L143 310\" stroke-width=\"19\"/><path class=\"b-fill\" d=\"M134 306 L160 304 C170 310 174 320 172 326 L132 326 Z\"/><path class=\"b-stroke\" d=\"M118 202 L113 254\" stroke-width=\"29\"/><path class=\"b-stroke\" d=\"M113 254 L108 316\" stroke-width=\"21\"/><path class=\"b-fill\" d=\"M92 314 L122 316 L124 332 L86 332 C86 323 88 315 92 314 Z\"/></g><g class=\"b-swing\"><path class=\"bat-trail\" d=\"M70.5 23.3 A110 110 0 1 0 232.9 115.2\"/><g class=\"b-arc\"><g class=\"b-dim\"><path class=\"b-stroke b-arm\" id=\"arm-back\" d=\"M108 118 L100 134 L94 102\" stroke-width=\"15\"/><path class=\"b-stroke b-arm\" id=\"arm-front\" d=\"M140 120 L130 136 L98 106\" stroke-width=\"15\"/></g><g class=\"b-reach\"><circle class=\"b-fill b-dim\" cx=\"96\" cy=\"102\" r=\"8\"/><polygon class=\"bat-handle\" points=\"92.4,104.7 99.6,99.3 79.1,66.5 68.8,73.6\"/><polygon class=\"bat-barrel\" points=\"68.8,73.6 79.1,66.5 54.1,26.3 39.9,35.7\"/><g class=\"contact-burst\" transform=\"translate(47,31)\"><g class=\"burst-rays\"><polygon points=\"7.0,2.6 25.0,0.0 7.0,-2.6\"/><polygon points=\"3.1,6.8 17.7,17.7 6.8,3.1\"/><polygon points=\"-2.6,7.0 0.0,25.0 2.6,7.0\"/><polygon points=\"-6.8,3.1 -17.7,17.7 -3.1,6.8\"/><polygon points=\"-7.0,-2.6 -25.0,0.0 -7.0,2.6\"/><polygon points=\"-3.1,-6.8 -17.7,-17.7 -6.8,-3.1\"/><polygon points=\"2.6,-7.0 -0.0,-25.0 -2.6,-7.0\"/><polygon points=\"6.8,-3.1 17.7,-17.7 3.1,-6.8\"/></g><circle class=\"burst-core\" r=\"6.5\"/></g></g></g></g></g>";
function mountOld(slot) {
  slot.innerHTML = OLD_MARKUP;
  const q = s => slot.querySelector(s), CF = 0.58, D = 900;
  const o = { duration: D, easing: "cubic-bezier(0.34, 0, 0.18, 1)" };
  const trail = q(".bat-trail"), L = trail.getTotalLength();
  trail.style.strokeDasharray = L;
  const anims = [
    q(".b-swing").animate([{ transform: "perspective(620px) rotateY(0deg)" }, { transform: "perspective(620px) rotateY(24deg)", offset: 0.34 }, { transform: "perspective(620px) rotateY(44deg)", offset: CF }, { transform: "perspective(620px) rotateY(50deg)", offset: 0.78 }, { transform: "perspective(620px) rotateY(0deg)" }], o),
    q(".b-reach").animate([{ transform: "translate(0px, 0px)" }, { transform: "translate(-5px, -3px)", offset: 0.34 }, { transform: "translate(-13px, -9px)", offset: CF }, { transform: "translate(-10px, -7px)", offset: 0.78 }, { transform: "translate(0px, 0px)" }], o),
    q("#arm-back").animate([{ d: 'path("M108 118 L100 134 L94 102")' }, { d: 'path("M108 118 L97 122 L83 93")', offset: CF }, { d: 'path("M108 118 L100 134 L94 102")' }], o),
    q("#arm-front").animate([{ d: 'path("M140 120 L130 136 L98 106")' }, { d: 'path("M140 120 L112 108 L85 97")', offset: CF }, { d: 'path("M140 120 L130 136 L98 106")' }], o),
    q(".b-arc").animate([{ transform: "rotate(12deg)" }, { transform: "rotate(-105deg)", offset: 0.34 }, { transform: "rotate(-195deg)", offset: CF }, { transform: "rotate(-232deg)", offset: 0.78 }, { transform: "rotate(0deg)" }], o),
    trail.animate([{ strokeDashoffset: L, opacity: 0 }, { strokeDashoffset: L * 0.92, opacity: 0.35, offset: 0.10 }, { strokeDashoffset: L * 0.45, opacity: 0.6, offset: 0.34 }, { strokeDashoffset: L * 0.12, opacity: 0.75, offset: CF }, { strokeDashoffset: 0, opacity: 0.45, offset: 0.78 }, { strokeDashoffset: 0, opacity: 0 }], o),
    q(".b-body").animate([{ transform: "perspective(620px) rotateY(0deg) rotate(0deg) translateY(0px)" }, { transform: "perspective(620px) rotateY(16deg) rotate(-2deg) translateY(3px)", offset: 0.30 }, { transform: "perspective(620px) rotateY(30deg) rotate(-5deg) translateY(7px)", offset: CF }, { transform: "perspective(620px) rotateY(34deg) rotate(-6deg) translateY(6px)", offset: 0.78 }, { transform: "perspective(620px) rotateY(0deg) rotate(0deg) translateY(0px)" }], o),
  ];
  anims.forEach(a => a.pause());
  return (ms, hit) => { const at = hit ? TRAVEL_MS - D * CF : 0; anims.forEach(a => { a.currentTime = Math.max(0, ms - at); }); };
}

function phaseAt(t) { let n = SWING[0].name; for (const k of SWING) if (t >= k.t - 1e-6) n = k.name; return n; }

function review() {
  const style = document.body.dataset.style, mount = document.getElementById("review");
  mount.innerHTML = `
    <div class="stage">
      <figure class="today"><figcaption>Today</figcaption><svg viewBox="12 20 350 360" aria-label="Today's swing"></svg></figure>
      <figure class="new"><figcaption>${document.querySelector("h1").textContent}</figcaption><svg viewBox="12 20 350 360" aria-label="The new swing"></svg></figure>
    </div>
    <div class="controls">
      ${PITCHES.map(p => `<button data-n="${p.n}">${p.n} ${p.kind}</button>`).join("")}
    </div>
    <div class="controls">
      <button class="play">Play</button>
      <input type="range" min="0" max="${END_MS}" step="1" value="0" aria-label="Pitch clock">
      <select aria-label="Speed">
        <option value="1">As it ships (slow motion ×2.1)</option>
        <option value="0.5">Half speed</option>
        <option value="0.2">One fifth</option>
        <option value="${SLOW}">Real time</option>
      </select>
      <label class="toggle"><input type="checkbox" class="cmp" checked> Show today</label>
      <span class="readout"></span>
    </div>
    <div class="strip"></div>`;
  const [oldSvg, newSvg] = mount.querySelectorAll(".stage svg");
  const setOld = mountOld(drawDiagram(oldSvg)), oldBall = mountBall(oldSvg);
  const draw = makeRig(drawDiagram(newSvg), style), newBall = mountBall(newSvg);

  const strip = mount.querySelector(".strip");
  for (const k of SWING) {
    const f = strip.appendChild(document.createElement("figure")); const svg = el("svg", null, f, { viewBox: "20 0 300 380" });
    makeRig(drawDiagram(svg), style)(k.t);
    const c = document.createElement("figcaption"); c.textContent = k.name; f.appendChild(c);
  }

  let clock = 0, playing = false, rate = 1, pitch = PITCHES[0], last = performance.now();
  const range = mount.querySelector("input[type=range]"), play = mount.querySelector(".play"), out = mount.querySelector(".readout");
  const render = () => {
    const hit = pitch.n === 1, t = swingTime(clock, hit), q = draw(t);
    newBall(clock, pitch, CONTACT); setOld(clock, hit); oldBall(clock, pitch, OLD_CONTACT);
    range.value = clock;
    out.innerHTML = `<b>${Math.round(clock)} ms</b> on screen · ${Math.round(clock / SLOW)} ms real · <b>${phaseAt(t)}</b>${q.strain > 0.02 ? " · grip strained" : ""}`;
    mount.querySelectorAll("[data-n]").forEach(b => b.setAttribute("aria-pressed", b.dataset.n == pitch.n));
  };
  const tick = now => {
    if (playing) { clock = Math.min(END_MS, clock + (now - last) * rate); if (clock >= END_MS) { playing = false; play.textContent = "Play"; } render(); }
    last = now; requestAnimationFrame(tick);
  };
  mount.querySelectorAll("[data-n]").forEach(b => b.addEventListener("click", () => {
    pitch = PITCHES[b.dataset.n - 1]; clock = 0; playing = true; play.textContent = "Pause"; render();
  }));
  play.addEventListener("click", () => { if (clock >= END_MS) clock = 0; playing = !playing; play.textContent = playing ? "Pause" : "Play"; });
  range.addEventListener("input", () => { clock = +range.value; playing = false; play.textContent = "Play"; render(); });
  mount.querySelector("select").addEventListener("change", e => { rate = +e.target.value; });
  mount.querySelector(".cmp").addEventListener("change", e => mount.querySelector(".stage").classList.toggle("solo", !e.target.checked));
  window.__review = { set: (ms, n) => { if (n) pitch = PITCHES[n - 1]; clock = ms; playing = false; render(); } };
  render(); requestAnimationFrame(tick);
}
if (document.getElementById("review")) review();
