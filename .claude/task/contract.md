# Task contract — competition header identity fields (→ green)

> Written on a CLEAN tree (branch feat/competition-header-identity off main @ 91bbcb1).
> Plan approved via ExitPlanMode this session. Export-only registry surfacing (the GAP-01 #613 pattern).

objective: >
  Make the competition-header block green: surface the registry identity fields `country`, `confederation`,
  `tier` on the competition-season hub payload. They already flow through `_registry_competitions` but are dropped
  when the `meta` dict is built in `fetch_competition_payloads`; the header today carries only name/slug/season.
  Pure registry pass-through — no BigQuery, no new fetch, no new model. CPO confirmed the {country, confederation,
  tier} field set via plan approval (mirrors GAP-01's CPO-ruled team founded/venue set).
refs: v2 board (content_architecture.md §3 "Competition header · partial"); GAP-01/#613 (team identity precedent); plan approved this session.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - docs/content_architecture.md
  - .claude/task/**

impact_map: >
  writers: none — no model/mart touched. Consumption layer only (`scripts/export_site_data.py`).
  downstream: `shape_competition_payload` feeds the `competitions` export entity (competitions.json hub). The
    three added fields are select/pass-through from the registry `meta` dict — NO derivation, NO computed facts
    (consumption-layer contract: the export may select/rename, never derive). GAP-01 (#613) is the precedent for
    surfacing registry/dim identity on an entity header.
  layer_rules: N/A (no dbt model). The consumption-layer contract applies — verified the change only selects
    existing registry values, computes nothing.
  deploy_order: NON-breaking. Export-only; the next pipeline export run emits the enriched competition payload.
    No dbt build, no --full-refresh, no migration ordering.
  blast_radius: `competitions.json` gains three top-level header fields (country/confederation/tier), None where a
    registry entry omits one (safe `.get`). No other entity payload changes; no number/metric moves; no data-build.

decisions_taken: >
  CPO-approved via the plan: surface {country, confederation, tier}. Excluded (not new decisions): competition_type/
  display_group (already power nav), sort_order (display constant), logo (not in the registry — provider-sourced,
  deferred). Folding the directly-coupled content_architecture.md §3 board flip (partial → green) into this PR
  follows the GAP-01 precedent; kept in scope per the plan.

decisions_reserved:
  - A full competition-page wireframe spec (none exists in 00–13) — a separate, later item; NOT this change.
  - Competition logo (provider-sourced) — deferred.

done_when:
  - `fetch_competition_payloads` meta dict carries country/confederation/tier; `shape_competition_payload` surfaces
    them in the returned payload (safe `.get`, None when absent).
  - A unit test in tests/test_export_site_data.py asserts the three fields surface from meta.
  - `python -m pytest tests/test_export_site_data.py -k competition` passes; python-ci green.
  - content_architecture.md §3 "Competition header" flipped partial → green.
  - scope-auditor + analytics-engineer + cto PASS (>=2 named risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
