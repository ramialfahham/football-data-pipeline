// The Filter bar's choices: a filter offers only the values its page's rows carry, and once the
// other filter is set, only the values that still leave a row. The radios are the bar's one state;
// the dropdowns follow them, and a dropdown's choice checks its radio.

/** The values a filter offers, in its own order: those at least one row carries. */
export function offered(order, carried) {
  const have = new Set(carried);
  return order.filter((v) => have.has(v));
}

/** Whether any row matches every set filter; an empty value matches every row. */
export function leavesARow(rows, want) {
  return rows.some((r) => Object.entries(want).every(([k, w]) => !w || r[k] === w));
}

function start() {
  for (const bar of document.querySelectorAll(".fbar")) {
    const scope = bar.parentElement;
    const rows = [...scope.querySelectorAll(".categories [data-entity-type], .categories [data-confederation]")]
      .map((e) => ({ entity: e.dataset.entityType || "", region: e.dataset.confederation || "" }));
    const names = ["entity-filter", "region-filter"].filter((n) => scope.querySelector(`input[name="${n}"]`));
    const key = { "entity-filter": "entity", "region-filter": "region" };
    const value = (n) => scope.querySelector(`input[name="${n}"]:checked`)?.value ?? "";
    const fits = (n, v) => leavesARow(rows, Object.fromEntries(names.map((m) => [key[m], m === n ? v : value(m)])));
    const full = Object.fromEntries(names.map((n) => {
      const sel = bar.querySelector(`select[data-filter="${n}"]`);
      return [n, sel ? [...sel.options].map((o) => [o.value, o.text]) : []];
    }));
    const sync = () => {
      for (const n of names) {
        const ok = (v) => !v || fits(n, v);
        const sel = bar.querySelector(`select[data-filter="${n}"]`);
        if (sel) {
          sel.replaceChildren(...full[n].filter(([v]) => ok(v)).map(([v, t]) => new Option(t, v)));
          sel.value = value(n);
        }
        for (const input of scope.querySelectorAll(`input[name="${n}"]`)) {
          input.disabled = !ok(input.value);
          const label = bar.querySelector(`label[for="${input.id}"]`);
          if (label) label.hidden = !ok(input.value);
        }
      }
    };
    scope.addEventListener("change", (e) => {
      const t = e.target;
      if (t instanceof HTMLSelectElement && t.dataset.filter) {
        const radio = scope.querySelector(`input[name="${t.dataset.filter}"][value="${t.value}"]`);
        if (radio) {
          radio.checked = true;
          radio.dispatchEvent(new Event("change", { bubbles: true }));
          return;
        }
      }
      if (t instanceof HTMLInputElement && names.includes(t.name)) sync();
    });
    sync();
  }
}

if (typeof document !== "undefined") start();
