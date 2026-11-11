// One rule for every block with a narrow form: a block keeps its wide form while its content fits on
// one line, and takes its narrow form otherwise, measured per block in the page's own language.
// The script marks each block `fit-one` or `fit-two`; system.css draws the two forms. A table fits
// when every name keeps its longest word inside its own space; a block of fact rows fits when its
// longest row (label, gap, value) fits its width; the header row fits when it holds the menu; a
// Filter bar fits when each row of buttons does, and its dropdown row when each holds its longest choice;
// a match row with a tag fits when its names keep their column beside the tag, each longest word
// inside its own space; a list of a player's matches fits when every row holds all its parts on one
// line, and so does a list of a team's results. A card block has three forms: it takes the first of one row and three across where every card
// holds its number and its longest word.

/** The width of a text's longest word, given a function that measures one word. */
export function longestWord(text, measure) {
  const words = String(text).trim().split(/\s+/).filter(Boolean);
  return words.length ? Math.max(...words.map(measure)) : 0;
}

/** The lists of result rows: a player's matches, a team's matches, and each column of a match's
 * Recent matches. Head to head and goal lists keep their width switch. */
export const RESULT_LISTS = ".rlist.pm, .rlist:has(.resrow:not(.meet, .goal, .scorer)), .rsplit > .rcol:has(.resrow:not(.meet, .goal, .scorer))";

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
  const names = (block, selector) => [...block.querySelectorAll(selector)].filter(shown)
    .map((nm) => ({ need: longestWord(nm.textContent, wordWidth(nm)), room: nm.clientWidth }));
  const measures = {
    table: (block) => names(block, ".ctab-row .tm .nm"),
    facts: (block) => [...block.children].filter((r) => r.classList.contains("frow") && shown(r))
      .map((row) => ({ need: oneLine(row), room: row.clientWidth })),
    header: (block) => [{ need: block.scrollWidth, room: block.clientWidth }],
    tagged: (block) => [...block.querySelectorAll(":scope > .sides")]
      .map((sides) => ({ need: sides.scrollWidth, room: sides.clientWidth }))
      .concat(names(block, ":scope > .sides .side .nm")),
    filter: (block) => [...block.children].filter((c) => c.matches(".seg:not(.sel)") && shown(c))
      .map((seg) => ({ need: seg.scrollWidth, room: seg.clientWidth })),
    selects: (block) => [...block.querySelectorAll(".sel-in")].filter(shown).map((sel) => {
      const s = getComputedStyle(sel);
      const width = wordWidth(sel);
      const longest = Math.max(0, ...[...sel.options].map((o) => width(o.text)));
      return { need: longest + parseFloat(s.paddingLeft) + parseFloat(s.paddingRight), room: sel.clientWidth };
    }),
    rows: (block) => [...block.querySelectorAll(".resrow")].filter(shown).map((row) => {
      const gap = parseFloat(getComputedStyle(row).columnGap) || 0;
      const need = [...row.children].reduce((sum, part) => sum + oneLine(part), 0) + gap * (row.children.length - 1) + 12;
      return { need, room: row.clientWidth };
    }),
    cards: (block) => {
      const grid = block.firstElementChild;
      const tiles = [...grid.children].filter(shown);
      const gap = parseFloat(getComputedStyle(grid).columnGap) || 0;
      const cols = parseInt(getComputedStyle(grid).getPropertyValue("--cols"), 10) || tiles.length;
      const room = Math.min(240, (grid.clientWidth - (cols - 1) * gap) / cols);
      return tiles.map((tile) => {
        const inner = getComputedStyle(tile.firstElementChild);
        const pad = parseFloat(inner.paddingLeft) + parseFloat(inner.paddingRight) + 2;
        // A label may take two lines and never breaks inside a word.
        const text = [...tile.querySelectorAll(".kpi-l, .kpi-n")].map((el) => {
          const width = wordWidth(el);
          return Math.max(longestWord(el.textContent, width), width(el.textContent.trim()) / 2);
        });
        const value = tile.querySelector(".kpi-v");
        return { need: pad + Math.max(wordWidth(value)(value.textContent.trim()), ...text), room };
      });
    },
  };
  const fit = (block, kind) => {
    if (!shown(block)) return;
    if (kind === "cards") {
      block.classList.toggle("narrow", block.clientWidth < 300);
      const take = (form) => {
        block.classList.remove("fit-one", "fit-two", "tight");
        if (form) block.classList.add(form);
        block.classList.toggle("tight", block.querySelector(".kpi").clientWidth < 100);
        return measures.cards(block);
      };
      for (const form of ["fit-one", "fit-two"]) {
        const rows = take(form);
        if (rows.length && fitsOneLine(rows)) return;
      }
      take(null);
      return;
    }
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
    ...[...document.querySelectorAll(".fxrow:has(> .topmatch)")].map((b) => [b, "tagged"]),
    ...[...document.querySelectorAll(".kpis")].map((b) => [b, "cards"]),
    ...[...document.querySelectorAll(RESULT_LISTS)].map((b) => [b, "rows"]),
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
