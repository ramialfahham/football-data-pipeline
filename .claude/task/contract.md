# Task contract — team page, Performance tab, from the approved mock

> Written on a CLEAN tree (branch `feat/team-page-performance` off main after #810 merged).

objective: >
  Build the team page Performance tab (mock `f6348775`, the second of its three tabs; Overview
  shipped in #810). Two panels behind a JS-free segment control: "vs the league" (the locked 16
  metrics, each with a direction-aware rank bar + median + rank label) and "vs last season" (the
  same 16 with signed year-over-year deltas). The CPO approved the plan (ExitPlanMode 2026-07-23).
  Frontend only — the benchmark and YoY data already ship in the committed sample; no export, dbt,
  or test change. Squad (the third tab) stays a coming-state (its per-player stats are #480).

refs: >
  Verified this session:
  - The locked 16-row contract already exists as `METRIC_ROWS` in `site_v2/src/lib/metricRows.ts`
    (field/group/tier/format/direction, from `docs/wireframes/metrics_display.md`) — reused verbatim.
  - The committed sample `site_v2/src/data/teams/33.json` already carries, per season, a `benchmarks`
    array (metric_key, metric_value, rank, team_count, league_median, p25/p75, vs_median_delta) and a
    `{field}_delta_yoy` for every one of the 16 rows. Only `save_ratio`'s YoY is null (en-dash).
  - The mart `rank` is RAW value-descending, NOT direction-aware (verified: goals-against value below
    median → raw rank 14/20). The frontend converts per `METRIC_ROWS.direction`, per metrics_display.md
    §Percentile. Presentation only.
  - The mock `f6348775` HTML/CSS (tool-results dir) is the design source; the Overview build (#810)
    established the pattern (transcribe CSS to system.css, reuse the JS-free `.seg-in` segment).

scope_paths:
  - site_v2/src/pages/[lang]/teams/
  - site_v2/src/components/team/
  - site_v2/src/styles/system.css
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/bars.ts
  - site_v2/src/lib/format.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/i18n/strings.ts
  - .claude/active_work.md

impact_map: >
  writers: none. No warehouse object, no dbt model, no export change. The benchmark rows
    (`mart_team_competition_benchmarks`) and the YoY `*_delta_yoy` / metric fields are ALREADY
    emitted by `shape_team_payload` and already present in the committed sample — this task only
    consumes them. `grep` confirms the team page is the only consumer.
  downstream: frontend only. New team components + appended team-Performance CSS blocks + small
    display helpers in `lib/bars.ts` / `lib/format.ts` (rank→position→width, ordinal, signed-delta
    formatting). The page swaps ONE coming-state div (Performance) for the built tab; Overview and
    Squad are untouched. Static Astro build; nothing deployed (no hosting), so no runtime blast radius.
  layer_rules: consumption-layer contract (Appendix A5) — the frontend selects, formats and maps to
    display (rank→bar width, direction→green) but derives no fact. The direction-aware rank conversion
    is the locked metrics_display.md §Percentile rule, not a new computation. No `check_layer_contract`
    gate on the site; the reviewers enforce it.
  deploy_order: none. Takes effect only when the page is built.
  blast_radius: bounded. Additive: new components, appended CSS (no shared block redefined —
    Performance blocks are new; the segment reuses the existing `.seg-in`), new lib helpers (additive
    exports), one swapped div. The fixture page and the Overview tab are unaffected. No data or
    warehouse change, so #805 binding is satisfied by construction (every rendered field already ships).

decisions_taken: >
  (1) BUILD the approved mock's Performance tab, reusing the locked `METRIC_ROWS` verbatim (do not
      re-author the contract). CPO approved the plan (ExitPlanMode, 2026-07-23).
  (2) Direction-aware rank/fill/green from the mart's raw value-descending `rank` + each row's
      `direction` (metrics_display.md §Percentile) — a display mapping, not a fact.
  (3) Drop the mock's interpretive per-panel lede this increment; keep only the factual caption.
      Recommended in the plan and approved with it; templating the lede is deferred.
  (4) JS-free segment control (reuse the existing `.seg-in` radio pattern), consistent with the
      Overview tabs — no client script.

decisions_reserved:
  - Whether to template the interpretive lede later is a display/narrative call — deferred, not
    decided away.
  - The Squad tab's data binding (#480 per-player stats) and its build are the next increment.
  - Per-locale metric ROW labels from the catalogue (#370): the rows use the locked EN labels for now,
    exactly as the fixture comparison does — not reopened here.

done_when:
  - The Performance tab renders in de/en/fi: the JS-free segment + both panels, all 16 rows grouped in
    the locked block order, the vs-league rank/fill/median direction-aware, the vs-last-season signed
    deltas (with `save_ratio` YoY as the en-dash), the defensive-actions `T · I · B` sublabel from the
    benchmark atoms.
  - The direction-aware rank/fill/green is correct on the lower-is-better and sparse rows (goals
    against, save %) — verified on the built HTML, not asserted.
  - `astro build` clean; `validate-local` Tier 1 green (pytest unaffected — no export change).
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments: (none)
