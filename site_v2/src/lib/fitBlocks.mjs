// One rule for every block with a narrow form: a block keeps its wide form while its content fits on
// one line, and takes its narrow form otherwise, measured per block in the page's own language.
// The script marks each block `fit-one` or `fit-two`; system.css draws the two forms. A table fits
// when every name keeps its longest word inside its own space; a block of fact rows fits when its
// longest row (label, gap, value) fits its width; the header row fits when it holds the menu; a
// Filter bar fits when each row of buttons does, and its dropdown row when each holds its longest choice.

/** The width of a text's longest word, given a function that measures one word. */
export function longestWord(text, measure) {
  const words = String(text).trim().split(/\s+/).filter(Boolean);
  return words.length ? Math.max(...words.map(measure)) : 0;
}

/** A block keeps one line when every row needs no more than its room (half a pixel of rounding). */
export function fitsOneLine(rows) {
  return rows.every(({ need, room }) => need <= room + 0.5);
}

function start() {
  const ctx = document.createElement("canvas").getContext("2d");
  const wordWidth = (el) => {
    const s = getComputedStyle(el);
    ctx.font = `${s.fontStyle} ${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
    return (word) => ctx.measureText(word).width;
  };
  const shown = (el) => el.getClientRects().length > 0;
  // The width a fact row needs on one line: a hidden copy laid out without wrapping, with the
  // row's own gap.
  const oneLine = (row) => {
    const copy = row.cloneNode(true);
    const gap = getComputedStyle(row).columnGap;
    copy.style.cssText = `display:flex;gap:${gap};width:max-content;position:absolute;visibility:hidden;left:0;top:0`;
    copy.querySelectorAll("*").forEach((x) => { x.style.whiteSpace = "nowrap"; });
    row.parentNode.appendChild(copy);
    const w = copy.getBoundingClientRect().width;
    copy.remove();
    return w;
  };
  const measures = {
    table: (block) => [...block.querySelectorAll(".ctab-row .tm .nm")].filter(shown)
      .map((nm) => ({ need: longestWord(nm.textContent, wordWidth(nm)), room: nm.clientWidth })),
    facts: (block) => [...block.children].filter((r) => r.classList.contains("frow") && shown(r))
      .map((row) => ({ need: oneLine(row), room: row.clientWidth })),
    header: (block) => [{ need: block.scrollWidth, room: block.clientWidth }],
    filter: (block) => [...block.children].filter((c) => c.matches(".seg:not(.sel)") && shown(c))
      .map((seg) => ({ need: seg.scrollWidth, room: seg.clientWidth })),
    selects: (block) => [...block.querySelectorAll(".sel-in")].filter(shown).map((sel) => {
      const s = getComputedStyle(sel);
      const width = wordWidth(sel);
      const longest = Math.max(0, ...[...sel.options].map((o) => width(o.text)));
      return { need: longest + parseFloat(s.paddingLeft) + parseFloat(s.paddingRight), room: sel.clientWidth };
    }),
  };
  const fit = (block, kind) => {
    if (!shown(block)) return;
    block.classList.remove("fit-two");
    block.classList.add("fit-one");
    const rows = measures[kind](block);
    if (!rows.length) return;
    const one = fitsOneLine(rows);
    block.classList.toggle("fit-one", one);
    block.classList.toggle("fit-two", !one);
  };
  const blocks = [
    ...[...document.querySelectorAll(".header-in")].map((b) => [b, "header"]),
    ...[...document.querySelectorAll(".ctab")].map((b) => [b, "table"]),
    ...[...new Set([...document.querySelectorAll(".frow")].map((r) => r.parentElement))].map((b) => [b, "facts"]),
    // the bar before its dropdown row: the row shows only once the bar has taken its narrow form
    ...[...document.querySelectorAll(".fbar")].map((b) => [b, "filter"]),
    ...[...document.querySelectorAll(".selbar")].map((b) => [b, "selects"]),
  ];
  const all = () => blocks.forEach(([b, kind]) => fit(b, kind));
  const kindOf = new Map(blocks);
  const observer = new ResizeObserver((entries) => entries.forEach((e) => fit(e.target, kindOf.get(e.target))));
  blocks.forEach(([b]) => observer.observe(b));
  // A tab or a fold shows a block that was hidden when the page loaded.
  document.addEventListener("change", all);
  document.fonts.ready.then(all);
  all();
}

if (typeof document !== "undefined") start();
