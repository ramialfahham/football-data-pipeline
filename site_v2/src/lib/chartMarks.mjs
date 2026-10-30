// A chart's marks keep their pixel size at every width: each circle carrying `data-px` (its radius
// in pixels) and `data-halo` (its halo in pixels) is rescaled to the drawing's current width.

function fit() {
  for (const svg of document.querySelectorAll("svg.dp-chart")) {
    const w = svg.getBoundingClientRect().width;
    if (!w) continue;
    const k = svg.viewBox.baseVal.width / w;
    for (const c of svg.querySelectorAll("circle[data-px]")) {
      c.setAttribute("r", String(Number(c.dataset.px) * k));
      if (c.dataset.halo) c.setAttribute("stroke-width", String(Number(c.dataset.halo) * 2 * k));
    }
  }
}

if (typeof document !== "undefined") {
  new ResizeObserver(fit).observe(document.body);
  document.addEventListener("change", fit);
  fit();
}
