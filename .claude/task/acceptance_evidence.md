# Acceptance evidence — drop the home page Browse section

> One line per declared criterion in `contract.md`, each read from BUILT output
> (`site_v2/dist/`, a fresh `npm run build`) or from an actually-executed command — never from
> source, never from `outerHTML`. Seven criteria declared; eight evidence lines below, because the
> built-HTML remnant check is recorded separately from the "renders Next matches only" reading —
> they are different observations of the built output, not one restated twice.
>
> ⚠ THE BULLETS BELOW ARE INDENTED 2sp ON PURPOSE. `_block()` in `git_discipline.py` collects lines
> under `criteria_demonstrated:` until the first NON-INDENTED non-empty line, so a bullet at column
> zero terminates the block immediately and the gate reads ZERO criteria. This is recorded in
> CLAUDE.md and it still caught this task once — the commit was denied "7 declared, 0 demonstrated"
> with all seven sitting right here, unindented.

criteria_demonstrated:

  - Home renders Next matches ONLY. Fresh `npm run build`, then parsed `site_v2/dist/en/index.html`:
    exactly ONE `<section>` element, and the only section-head label in the built markup is
    "Next matches". The live accessibility tree showed `region` (fixtures hero) followed IMMEDIATELY
    by `contentinfo` (footer), nothing between, so no empty wrapper or margin-only gap was left
    behind. Detail in `rendered_page_evidence.md`.
  - No Browse remnants in the built HTML, ALL THREE locales.
    `grep -c -iE "browse|linkchip|subhead"` against `dist/en/index.html`, `dist/de/index.html` and
    `dist/fi/index.html` after the fresh build returns 0, 0, 0 — covering the block, its chip class
    and the orphaned `.subhead` rule in one pass, read from the artefact rather than the templates.
  - `landing.json` carries exactly `{type, upcoming}`. `json.load` on
    `site_v2/src/data/landing.json` printed `['type', 'upcoming']`; the `browse` key is gone from the
    committed payload, not merely unread by the page.
  - `astro build` succeeds clean: 60 pages built, `audit-seo: 61 built page(s) checked. OK.`, zero
    errors and no new warnings. That audit is the gate that fails on a dead internal link, so a
    surviving Browse chip pointing at a non-built page would have turned it red.
  - `pytest tests/test_export_landing.py` passes against the new signature: 8 passed. Full suite also
    run: 829 passed, 1 skipped, 14 subtests passed. Both payload-shape tests moved in lockstep — the
    exact key-set assertion is now `{"type", "upcoming"}` and a new `assert "browse" not in payload`
    pins the removal by name, so a revert fails rather than passing silently.
  - Zero `BrowseGrid.astro` references repo-wide. `grep -rn "BrowseGrid"` excluding
    `node_modules`/`.git`/`dist`/`.claude/task` paperwork returns no files; every prose mention was
    deleted or rephrased to describe the component without citing the dead filename.
  - `nav.json` still produces output, untouched. Executed `fetch_nav()` directly: returned 4 groups
    and 18 countries, and `scripts/export_site_data.py:1360` still carries its own
    `if "nav" in entities:` dispatch branch — confirming `build_nav`/`fetch_nav` survived as an
    independent export target rather than being removed with the block that consumed them.
  - No surviving claim that Browse exists, literal OR paraphrased. Two sweeps. Literal:
    `grep -rn -i browse` repo-wide, every hit triaged to one of three permitted classes (the English
    word "browser"; the still-live `08_browse.md`/competitions index; the struck-through record of
    the decision). Semantic, added after `mart_competition_index.sql` was caught asserting
    `sort_order` was "still live on the home page" WITHOUT using the word:
    `grep -rn -iE "(still live|feeds the|renders the|consumed by).{0,50}(home|landing)"` now returns
    nothing, and each machinery identifier (`display_group`, `build_nav`, `nav.json`, `_GROUP_ORDER`,
    `_DOMESTIC_TYPES`, `linkchip`, `country hub`) was read in context rather than counted.

## Not covered here

Per-locale geometry was not re-measured at a fixed viewport. No new content needs its height pinned —
a block was deleted, not resized or reordered — so the page is simply shorter by whatever Browse
occupied. `dist/de` and `dist/fi` were grepped (above) but not read structurally the way `dist/en`
was; the same `shape_landing_payload` output feeds all three, and the removed i18n keys were verified
deleted from all three locale blocks in `strings.ts` directly.
