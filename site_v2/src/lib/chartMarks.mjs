// A chart drawing's text and marks keep their system.css size at every width: each element carrying
// `data-fix` (its own transform, if any) is scaled back by the drawing's current scale around its
// anchor point. A label marked `data-role="gap"` then takes the height nearest the team's dot, on
// the side the build gave it, where it meets no line, dot, axis or other label: its size is fixed
// on screen while the drawing scales, so no height chosen at build time is clear at every width.

function scale(el, k) {
  const x = Number(el.getAttribute("cx") ?? el.getAttribute("x") ?? 0);
  const y = Number(el.getAttribute("cy") ?? el.getAttribute("y") ?? 0);
  el.setAttribute("transform", `${el.dataset.fix} translate(${x} ${y}) scale(${k}) translate(${-x} ${-y})`.trim());
}

const rect = (el) => el.getBoundingClientRect();
const meets = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;

function segmentMeets(svg, line, r, pad = 1) {
  const m = svg.getScreenCTM();
  const at = (x, y) => new DOMPoint(Number(line.getAttribute(x)), Number(line.getAttribute(y))).matrixTransform(m);
  const a = at("x1", "y1"), b = at("x2", "y2");
  const l = r.left - pad, t = r.top - pad, rr = r.right + pad, bb = r.bottom + pad;
  const inside = (p) => p.x > l && p.x < rr && p.y > t && p.y < bb;
  if (inside(a) || inside(b)) return true;
  const side = (p, q, s) => (s.x - p.x) * (q.y - p.y) - (s.y - p.y) * (q.x - p.x);
  const cross = (p, q, s, u) => (side(s, u, p) > 0) !== (side(s, u, q) > 0) && (side(p, q, s) > 0) !== (side(p, q, u) > 0);
  const c = [{ x: l, y: t }, { x: rr, y: t }, { x: rr, y: bb }, { x: l, y: bb }];
  return c.some((s, i) => cross(a, b, s, c[(i + 1) % 4]));
}

function dotMeets(dot, r) {
  const d = rect(dot), cx = (d.left + d.right) / 2, cy = (d.top + d.bottom) / 2, rad = (d.right - d.left) / 2;
  const nx = Math.max(r.left, Math.min(cx, r.right)), ny = Math.max(r.top, Math.min(cy, r.bottom));
  return (nx - cx) ** 2 + (ny - cy) ** 2 < rad * rad;
}

function hits(svg, el, box, skip) {
  const r = rect(el);
  let n = 0;
  if (r.left < box.left || r.right > box.right || r.top < box.top || r.bottom > box.bottom) n++;
  for (const line of svg.querySelectorAll("line")) if (segmentMeets(svg, line, r)) n++;
  for (const dot of svg.querySelectorAll("circle")) if (dotMeets(dot, r)) n++;
  for (const text of svg.querySelectorAll("text")) if (text !== el && text !== skip && meets(rect(text), r)) n++;
  return n;
}

// Under the name, the two labels stack beside the dot; where the drawing has no room below the name
// (a dot near the x axis), the name may rise, provided it then meets nothing itself.
const LIFTS = [0, 0.25, 0.5, 0.75, 1];

function place(svg, k) {
  const label = svg.querySelector('[data-role="gap"]');
  const name = svg.querySelector('[data-role="name"]');
  const dot = svg.querySelector(".chart-me");
  if (!label || !dot) return;
  for (const t of [label, name]) if (t) t.dataset.y0 ??= t.getAttribute("y");
  const box = rect(svg);
  const set = (t, y) => { t.setAttribute("y", String(y)); scale(t, k); };
  const under = !!name && label.getAttribute("text-anchor") === name.getAttribute("text-anchor")
    && label.getAttribute("dx") === name.getAttribute("dx");
  const y0 = Number(label.dataset.y0);
  set(label, y0);
  if (name) set(name, Number(name.dataset.y0));
  const start = rect(label), h = start.bottom - start.top, d = rect(dot);
  const toDot = ((d.top + d.bottom) / 2 - (start.top + start.bottom) / 2) * k;
  let best = { lift: 0, y: y0, n: hits(svg, label, box) };
  for (const lift of under ? LIFTS : [0]) {
    if (!best.n) break;
    if (lift) {
      set(name, Number(name.dataset.y0) - lift * h * k);
      if (hits(svg, name, box, label)) continue;
    }
    for (let i = 0; best.n && i <= 32; i++) {
      const y = y0 + toDot + (i % 2 ? 1 : -1) * Math.ceil(i / 2) * h * 0.25 * k;
      set(label, y);
      const n = hits(svg, label, box);
      if (n < best.n) best = { lift, y, n };
    }
  }
  if (name) set(name, Number(name.dataset.y0) - best.lift * h * k);
  set(label, best.y);
}

function fit() {
  for (const svg of document.querySelectorAll(".chart svg[viewBox]")) {
    const w = svg.getBoundingClientRect().width;
    if (!w) continue;
    const k = svg.viewBox.baseVal.width / w;
    for (const el of svg.querySelectorAll("[data-fix]")) scale(el, k);
    place(svg, k);
  }
}

if (typeof document !== "undefined") {
  // A tab or a toggle shows a drawing on its `change`, fitted at once; each drawing is also watched,
  // so a change of width fits it. A resize is reported only on a rendered frame, which a page the
  // browser is not painting never gets.
  document.addEventListener("change", fit);
  const watch = new ResizeObserver(fit);
  for (const svg of document.querySelectorAll(".chart svg[viewBox]")) watch.observe(svg);
  fit();
}
