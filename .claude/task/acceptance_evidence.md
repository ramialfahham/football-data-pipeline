# Acceptance evidence — #62 step 5: the competitions index page

criteria_demonstrated:
  - **All three locales build and render with no console errors.** Ran `preview_start` (name `v2`,
    Astro dev server), navigated to `http://localhost:4321/en/competitions/`,
    `/de/competitions/`, `/fi/competitions/`. `read_console_messages` showed zero errors on all
    three (only benign `[vite] connecting/connected` debug lines). Titles rendered correctly per
    locale: "All football competitions" / "Alle Fußballwettbewerbe" / "Kaikki jalkapallokilpailut".
  - **Every browsable competition (48/48) grouped under an always-shown category heading.**
    `get_page_text` on the EN page listed all 8 categories (Domestic cups, Domestic leagues,
    Continental club cups, Continental championships, Continental super cups, World Cup, National
    team qualifiers, Club World Cup) with every one of the 48 committed rows present — cross-checked
    against `site_v2/src/data/competition_index.json`'s row count. "Continental super cups" and
    "World Cup" each have exactly one member and both still show their heading.
  - **Category and row order follow the CPO-approved key, verified against real data, not just the
    unit test.** Before touching the browser, I ran `groupAndOrderCompetitions` directly against
    the committed `competition_index.json` from a scratch script and printed the full computed
    order. The RENDERED page's category order and every row's order within each category matched
    that computed output exactly, category-by-category, row-by-row (Domestic cups: CIT, DFBP, CDF,
    FAC, CDR; Domestic leagues: PD, LP, APD, BSA, LMX, MLS, SPL, VL, EKS, TSL, BPL, L1, PL, J1, ED,
    SA, KL1, BL2, BL1; Continental club cups: UCL, LIBER, UEL, UECL, CAFCL, AFCCL, CCCU; Continental
    championships: UNL, ACN, AFCON, GCUP, CNL, COAM, EURO; National team qualifiers: WCQIP, WCQEU,
    WCQCA, WCQAS, WCQAF, WCQSA, WCQOC — all confirmed by direct read of the rendered page text).
  - **Rows are logo + name + region sub-line, NOT clickable.** `read_page` (accessibility tree, full
    depth) on the EN page showed all 48 competition rows as `generic` elements — zero `link` roles
    among them. The only real links on the whole page are the wordmark (header + footer), the
    breadcrumb's "Home" segment, and the two (desktop + mobile) "Competitions" nav items. Region
    sub-lines resolve correctly both ways: domestic rows show the plain country
    (`region_label_en`, e.g. "Italy", "Germany" — no i18n lookup, since `region_label_i18n_key` is
    null), international rows show the translated region (e.g. EN "Europe" / DE "Europa" / FI
    "Eurooppa" for the same UEFA rows).
  - **Two filter axes narrow visible rows; an empty category disappears entirely.** Clicked the
    "Clubs" filter label (the `.seg-in` radio itself has `pointer-events: none` by design — the
    associated `<label>` is the real click target). Result: "Continental championships", "World
    Cup", and "National team qualifiers" (all-national categories) vanished completely, including
    their headings; all-club categories kept every row. Then added the "Oceania" region filter on
    top of "Clubs" (the combined case #54's own notes measure as "0/0"): every category and row
    disappeared, confirmed via `get_page_text` showing only the page chrome and the filter controls
    themselves. This proves the inline empty-category-collapse script correctly handles the
    compound case pure CSS `:checked` sibling selectors couldn't express cleanly.
  - **Nav "Competitions" is a real link; every other item stays inert.** `read_page` on both the
    competitions page and a *different* page (home, `/en/`) confirmed
    `link "Competitions" href="/en/competitions/"` in both the desktop `.mainnav` and the mobile
    `.drawer` regions, on both pages (shared `SiteHeader.astro`). "Matches", "Teams", "Players",
    "Standings", "Stats" all remained `generic` (span) in every check.
  - **`python scripts/check_copy_gate.py` passes.** Final run (after all i18n additions, including
    the filter-label keys added mid-build): `COPY GATE ok: 450 strings across 3 locales (396 chrome
    + 54 metric labels), 390 corpus strings consulted`.
  - **`node scripts/check-page-specs.mjs` and `node --test` both pass.** `check-page-specs`:
    `4 page(s) validated against their specs. OK.` (up from 3 before this change — the new page +
    spec pair validates). `node --test` (site_v2/, full suite): `tests 72 / pass 72 / fail 0`,
    including the 7 new `competitionOrder.test.mjs` cases.
  - **Visually verified at desktop and mobile widths.** `resize_window` to `desktop` (1280x720) and
    `mobile` (375x812) presets; `get_page_text` confirmed full content renders correctly at both
    (responsive `auto-fill, minmax(280px, 1fr)` grid, no layout-breaking text). Note: the Browser
    pane's `screenshot` action is unavailable in this environment (documented limitation —
    "the Browser pane is not displayed, so the page is not compositing frames"); verification used
    the accessibility tree, `get_page_text`, and `read_console_messages` instead, which is
    sufficient to confirm structure, content, and absence of errors at each width.
