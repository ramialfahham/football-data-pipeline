// A separator dot never starts a line. wholeWords.mjs wraps every middle dot between items in a
// `[data-dot]` span that holds the dot and the space after it, so the dot never ends a line either. This
// script hides a dot whose item moved to its own line: the dot's box sits below the text before it.
// The page reads the same without the script, with the dot at the start of the line.

/** True when the dot sits on a later line than the text before it. Boxes are [top, bottom]. */
export function startsLine(dot, before) {
  return before === null || dot[0] >= before[1] - 1;
}

const BLOCKLESS = new Set(["inline", "inline-block", "contents"]);

function start() {
  const shown = (el) => el.getClientRects().length > 0;
  const container = (dot) => {
    let el = dot.parentElement;
    while (el.parentElement && BLOCKLESS.has(getComputedStyle(el).display)) el = el.parentElement;
    return el;
  };
  // The last line box of the nearest text before the dot that is on the page.
  const before = (dot) => {
    const walker = document.createTreeWalker(container(dot), NodeFilter.SHOW_TEXT);
    walker.currentNode = dot;
    for (let n = walker.previousNode(); n; n = walker.previousNode()) {
      if (!n.textContent.trim() || n.parentElement.closest("[data-dot]") || !shown(n.parentElement)) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      const rects = range.getClientRects();
      if (rects.length) {
        const last = rects[rects.length - 1];
        return [last.top, last.bottom];
      }
    }
    return null;
  };
  const run = () => {
    const dots = [...document.querySelectorAll("[data-dot]")];
    dots.forEach((d) => { d.hidden = false; });
    for (const d of dots) {
      if (!shown(d)) continue;
      const rect = d.getClientRects()[0];
      if (startsLine([rect.top, rect.bottom], before(d))) d.hidden = true;
    }
  };
  if (!document.querySelector("[data-dot]")) return;
  new ResizeObserver(run).observe(document.body);
  document.addEventListener("change", run);
  document.fonts.ready.then(run);
  run();
}

if (typeof document !== "undefined") start();
