# Acceptance evidence — the menu's last item reads Leaderboards

Read from `site_v2/dist` built by `npm run build` on the committed sample (1,195 pages;
`audit-seo: 1195 built page(s) checked. OK.`), with a scratchpad script that strips Astro's
`<!-- -->` splits, takes each page's header nav and footer, and reads the last menu item's text
and link state. Exit codes read bare.

criteria_demonstrated:
  - EVERY BUILT PAGE SHOWS THE NEW WORD, IN ITS OWN LANGUAGE, AND NO PAGE SHOWS THE OLD ONE.
    Swept all 1,195 pages under `dist`; 1,194 carry the header nav (the 1,195th is the root
    redirect stub, which has no chrome). The last menu item reads `Leaderboards` on 398 pages,
    `Bestenlisten` on 398 and `Kärkilistat` on 398 — the three locales, evenly. Pages still
    showing `Stats`, `Statistiken` or `Tilastot` in the nav or the footer link row: **0**.
    `grep -rn "navStats"` over the tree returns only this contract's own account of the old key.
  - THE ITEM IS STILL DEAD TEXT. Of the 1,194 pages with a nav, the last item renders without an
    `href` on **1,194** — a `<span>`, as before. No page gained a link, so nothing points at the
    hub #139 has not built, and `audit-seo`'s internal-link resolution is unaffected
    (`audit-seo: 1195 built page(s) checked. OK.`).
  - THE GATES ARE GREEN. `python scripts/check_copy_gate.py` → `COPY GATE ok: 654 strings across
    3 locales (555 chrome + 99 metric labels)`, exit 0. `python scripts/check_ui_i18n_metrics.py`
    exit 0. `cd site_v2 && npm test` → 99 pass, 0 fail. `python -m pytest
    tests/test_governance_hooks.py tests/test_design_mock_renders.py -q` → 316 passed.
    `python scripts/check_design_inventory.py --dist site_v2/dist` → `19 pages · 2 viewports · 2
    languages · 76 renders · 0 failures · 0 warnings`, exit 0.

⚠ Not demonstrated here, and pre-existing: `design-mocks/gen_navmap.py` aborts on its own
assertion `not nav_is_link` ("the nav now emits anchors -- this page says it does not"), because
Competitions became a link when #128 built the competitions index and the diagram's prose still
says the nav is inert. Confirmed on `main` with this branch's files stashed: the same assertion
fires. The generator is a diagram, not in `block_standard.md`'s Pages table, so no check runs it.
This branch's edit to it (the key rename) is verified directly instead: `menu_items()` returns the
six keys ending `('navLeaderboards', 'Leaderboards')` and every key resolves to a `MENU_NOTES`
entry.
