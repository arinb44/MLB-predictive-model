/* Reproduces the geometry of drawRanked() in src/api/static/index.html so the
   mockup's chart is faithful rather than hand-drawn. Same classes, same maths. */
const MLB_ID = {NYY:147,KCR:118,LAD:119,BOS:111,BAL:110,NYM:121,ARI:109,CIN:113,SDP:135,
  TEX:140,CLE:114,MIL:158,TOR:141,HOU:117,ATL:144,PHI:143,CHC:112,DET:116};
const cap = c => `https://www.mlbstatic.com/team-logos/team-cap-on-dark/${MLB_ID[c]}.svg`;

export function drawRanked(rows, {W = 1064, metric, fmt, marker = "dot"}) {
  const useLogo = marker === "logo";
  const rowH = useLogo ? 30 : 22;
  const narrow = W < 520;
  const labelW = narrow ? 118 : 190;
  const maxChars = narrow ? 14 : 24;
  const mg = {top: 26, right: 48, bottom: 8, left: labelW};
  const H = mg.top + rows.length * rowH + mg.bottom;
  const vals = rows.map(r => r.v);
  const lo = Math.min(0, ...vals), hi = Math.max(...vals) * 1.04;
  const x = v => mg.left + (v - lo) / (hi - lo) * (W - mg.left - mg.right);
  const base = lo;
  const ticks = [];
  const step = (hi - lo) / (narrow ? 3 : 5);
  for (let t = lo; t <= hi + 1e-9; t += step) ticks.push(t);

  let s = `<svg viewBox="0 0 ${W} ${H}" height="${H}" role="img" aria-label="${metric} dot plot">`;
  for (const t of ticks) {
    s += `<line class="gridline" x1="${x(t).toFixed(1)}" x2="${x(t).toFixed(1)}" y1="${mg.top - 6}" y2="${H - mg.bottom}"/>`;
    s += `<text class="dim" x="${x(t).toFixed(1)}" y="${mg.top - 12}" text-anchor="middle">${fmt(t)}</text>`;
  }
  rows.forEach((r, i) => {
    const cy = mg.top + i * rowH + rowH / 2;
    s += `<g class="hit">`;
    if (i % 2 === 1) s += `<rect class="stripe" x="0" y="${cy - rowH / 2}" width="${W}" height="${rowH}"/>`;
    s += `<text class="dim" x="4" y="${cy + 4}">${i + 1}</text>`;
    s += `<image href="${cap(r.team)}" x="26" y="${cy - 8}" width="16" height="16"/>`;
    const shown = r.name.length > maxChars ? r.name.slice(0, maxChars - 1) + "\u2026" : r.name;
    s += `<text x="52" y="${cy + 4}">${shown}</text>`;
    s += `<line class="stem" x1="${x(base).toFixed(1)}" x2="${x(r.v).toFixed(1)}" y1="${cy}" y2="${cy}"/>`;
    if (useLogo) {
      s += `<image href="${cap(r.team)}" x="${(x(r.v) - 13).toFixed(1)}" y="${cy - 13}" width="26" height="26"/>`;
    } else {
      s += `<circle cx="${x(r.v).toFixed(1)}" cy="${cy}" r="6" fill="var(--accent)" stroke="var(--bg)" stroke-width="1.5"/>`;
    }
    const off = useLogo ? 17 : 10;
    s += `<text class="dim" x="${(x(r.v) + off).toFixed(1)}" y="${cy + 4}" text-anchor="start">${fmt(r.v)}</text>`;
    s += `</g>`;
  });
  return s + `</svg>`;
}
