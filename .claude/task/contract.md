# Task contract — #62 step 5: the competitions index page

objective: >
  Build `/{locale}/competitions/`: the page-spec, the Astro page + component, the CPO-approved
  ordering logic, the committed data file, i18n for the categories/regions it renders, and the
  `SiteHeader` nav anchor swap. Last of #62's five steps. The design is already fully settled
  (GitLab #54, CPO-reviewed 2026-08-10 with corrections through 2026-08-17, plus the 2026-08-16
  ordering ruling in `escalations.log`) — this is faithful implementation, not new design.
refs: GitLab #62 (step 5 of 5), #54 (page design), #52 (interaction standard), #50 (block
  standard), #47 (competition hub — confirmed NOT built, shapes the row-link decision below)

scope_paths:
  - site_v2/src/data/competition_index.json
  - site_v2/src/data/README.md
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/competitionOrder.ts
  - site_v2/src/lib/competitionOrder.mjs
  - site_v2/src/lib/competitionOrder.test.mjs
  - site_v2/src/specs/page-spec.schema.json
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/src/specs/competitions/index.spec.json
  - site_v2/src/components/competitions/CompetitionIndexGrid.astro
  - site_v2/src/pages/*/competitions/index.astro
  - site_v2/src/components/chrome/SiteHeader.astro
  - site_v2/src/styles/system.css
  - docs/wireframes/08_browse.md
  - docs/wireframes/00_overview.md
  - docs/site_architecture.md
  - .claude/active_work.md

acceptance_criteria:
  - `/en/competitions/`, `/de/competitions/`, `/fi/competitions/` all build and render with no
    console errors.
  - The page shows every "browsable" competition in `competition_index.json` (48 rows, all of
    them — the mart already excludes non-browsable types) grouped under a category heading per
    `competition_type` present in the data; a category with only one member still shows its
    heading (never hidden).
  - Category order AND within-category row order both follow the CPO-approved key
    (`escalations.log`, 2026-08-16): has-upcoming-fixture, then days-to-next-kickoff bucketed by
    calendar day, then `region_rank`, then kickoff time, then `league_code`; no-upcoming rows sort
    last, most-recently-played first; categories order by their own earliest-sorting member.
    Verified by hand-computing the expected order for a handful of real rows and checking the
    rendered page matches.
  - Each row shows the competition's logo, name, and region sub-line (`region_label_en` when
    `region_label_i18n_key` is null — a country — else the translated region label). Rows are
    NOT yet clickable links — matching `BrowseGrid.astro`'s established "no dead links until the
    target page exists" precedent, since #47 (the competition hub each row would link to) is
    confirmed not built.
  - Two filter controls (`entity_type`: clubs/national; `confederation`: region) narrow the
    visible rows via the existing zero-JS `segment`/`seg-btn` CSS pattern (no client JS); a
    category left with zero visible rows after filtering disappears entirely, no empty-state
    placeholder.
  - The site nav's "Competitions" item is a real `<a href="/{locale}/competitions/">` in both the
    desktop nav and the mobile drawer; every other nav item stays an inert `<span>`.
  - `python scripts/check_copy_gate.py` passes (all new i18n keys present, real DE/FI
    translations, no byte-identical-to-English non-brand values).
  - `node scripts/check-page-specs.mjs` and `node --test` (site_v2/) both pass.
  - Visually verified in the Browser pane at desktop and mobile widths, screenshotted.

impact_map: >
  writers: `competition_index.json` is committed from a real, already-priced (10,067 bytes)
    `python scripts/export_site_data.py --entities competition_index` run against prod
    `mart_competition_index` (merged !65, live). No export code changes in this task — the
    committed file is a snapshot, refreshed the same way `landing.json`/`teams/*.json` already
    are per `site_v2/src/data/README.md`'s "refresh as a set" convention.

  downstream: NEW page, NEW component — nothing existing depends on them. `site_v2/src/lib/types.ts`
    gains one new additive interface (`CompetitionIndexRow`/`CompetitionIndex`); no existing
    interface is changed. The `SiteHeader.astro` nav change is the only edit to an already-shipped,
    already-rendered surface: every other page that imports `SiteHeader` (home, team, fixture)
    picks up the anchor swap automatically since it's the same shared component — confirmed via
    `grep -rln "SiteHeader" site_v2/src` before editing, and at least one non-competitions page
    (home) screenshotted to confirm the nav still renders correctly elsewhere.

  layer_rules: this is entirely the consumption/presentation layer (site_v2/src/**) — no dbt
    model, no export Python change. The CPO's consumption-layer rule (select/filter/group/rename/
    format only, never compute) governs `CompetitionIndexGrid.astro`: it renders what
    `competition_index.json` already carries. `competitionOrder.ts` is the one place doing real
    logic (a sort), which is correct per the CPO's own 2026-08-16 ruling that ordering is the
    PAGE's job, explicitly not the mart's or the export's — quoted in the file's header comment.

  deploy_order: none — this MR does not wire `competition_index` into
    `.gitlab-ci.yml`/`deploy-site-v2.yml`'s `--entities` list (deliberately reserved, see below),
    so the committed sample is what both local dev and any future CI build read; no BigQuery
    dependency at build time for this page.

  blast_radius: additive except `SiteHeader.astro` (nav swap, scoped to one array entry),
    `types.ts` (additive interface), and the two `entity` enum files (additive value, no existing
    value changed). No other page's markup, data, or route changes.

decisions_taken: >
  Three things #54 left open, resolved WITH the user before this contract was written (this
  session, not a silent call):

  1. PAGE WIDTH: `.inner`'s 680px→1080px override was flagged in #54's own text as "a
     system-level decision, not a page one... flagged for a ruling," never actually ruled on.
     Decided: ship at the standard 680px width, two-column layout. No `system.css` measure
     changes.

  2. FILTERS: #54 states the mock's single-select is "a pure-CSS limit of the mock, not the
     design... the shipped Astro page has JS and can multi-select." Decided: single-select now
     (existing zero-JS `segment`/`seg-btn` radio pattern), multi-select JS as a follow-up — ships
     faster, matches the mock exactly, no new interaction code in an already-large change.

  3. ROW LINKS: #54 describes rows as real links to each competition's own page. Checked GitLab
     #47 directly: `state: opened`, not built — only the fixture page exists under
     `site_v2/src/pages/[lang]/[competition]/`. #47's own issue text repeatedly names linking to
     a page that doesn't exist as "the browse-chip 404" failure mode, which is exactly why
     `BrowseGrid.astro`'s chips are inert `<span>`s today. Decided: ship rows inert (full content,
     no anchor, no hover-lift, no chevron — those affordances would falsely signal clickability),
     becoming real links in the MR that ships #47, mirroring `BrowseGrid.astro`'s own documented
     pattern exactly.

  NEW MECHANISM: none — reuses the existing zero-JS filter pattern, the existing `t()`/i18n
  machinery, the existing page-spec schema (widened by one enum value), the existing `Layout`/
  `SiteHeader` components. RECURRING COST: none — one more static JSON file in a build that
  already runs.

decisions_reserved:
  - Wiring `competition_index` into `.gitlab-ci.yml`/`deploy-site-v2.yml`'s `--entities` list —
    deliberately NOT done here (contract for #62 step 4 already reserved this the same way).
    Nothing outside this MR reads the committed file's freshness guarantee yet, so there is
    nothing to wire it to; revisit when a real deploy needs a live-refreshed sample.
  - Multi-select filtering (JS) — explicitly reserved to a follow-up per decision 2 above.
  - Making rows real links — explicitly reserved to the MR that ships #47 per decision 3 above.
  - The `entity` enum value name (`competitionIndex`) is a technical schema categorisation
    decision, not user-facing copy — made here, not escalated, consistent with how the Python
    export's `"competition_index"` entity-type name was decided without escalation in step 4.

done_when:
  - Every item in `acceptance_criteria` above is demonstrated and recorded in
    `.claude/task/acceptance_evidence.md` under a `criteria_demonstrated:` marker, read from
    built output (not asserted).
  - `node --test` (site_v2/) green, including the new `competitionOrder.test.mjs`.
  - `python scripts/check_copy_gate.py` and `node scripts/check-page-specs.mjs` both pass.
  - `docs/wireframes/08_browse.md` written per the standard §1–§10 template; `00_overview.md`'s
    screen-inventory row flipped from "pending" to a link.
  - `.claude/active_work.md` updated in the same commit, under 16,000 characters.

amendments:
  - 2026-08-18: + site_v2/src/lib/types.ts — authority: mechanical addition, caught by the
    contract gate on first edit attempt (the new CompetitionIndexRow/CompetitionIndex interfaces
    belong beside every other page's types in the same file, per existing convention). No CPO
    judgment call involved; recorded per §2's amendment process on a clean tree before proceeding.
  - 2026-08-18: corrected `site_v2/src/pages/[lang]/competitions/index.astro` to
    `site_v2/src/pages/*/competitions/index.astro` in scope_paths — authority: mechanical fix,
    caught by the contract gate on the actual page-file write attempt. `[lang]` is a literal
    directory name in Astro's routing convention but the gate's fnmatch reads `[...]` as a
    character class (matches one of l/a/n/g), the exact trap CLAUDE.md documents for
    `[lang]`/`[team]` segments. No CPO judgment call; recorded on a clean tree before proceeding.
  - 2026-08-18: corrected `site_v2/src/components/layout/SiteHeader.astro` to
    `site_v2/src/components/chrome/SiteHeader.astro` in scope_paths — authority: mechanical fix,
    the component lives under `components/chrome/` (confirmed by reading `Layout.astro`'s own
    import), not `components/layout/`, which I misremembered while drafting the contract before
    reading the real file. No CPO judgment call; recorded on a clean tree before proceeding.
  - 2026-08-18: + `site_v2/src/lib/competitionOrder.mjs` — authority: platform-reviewer round-1
    FAIL. `competitionOrder.ts` (deleted, its scope_paths entry stays to permit the delete) was
    the only place in the codebase where a `node:test` file imports a `.ts` file directly; every
    other test that needs something from a `.ts` file text-scans it instead
    (`check-metric-labels.test.mjs`'s own documented reason: `node --test` cannot import `.ts`
    without relying on Node's native type-stripping being on by default, which the repo's declared
    `engines: >=22` floor does not guarantee — only Node ≥22.18/≥23.6 default it on). Converted the
    module to plain `.mjs` (JSDoc instead of TS types) so neither the test nor Astro's own build
    depend on that capability. No CPO judgment call — a portability fix matching an existing,
    documented house convention; recorded on a clean tree before proceeding.
