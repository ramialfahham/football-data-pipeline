# Task contract — #391 GAP-01: team founded year + venue on the v2 team profile

> Written on a CLEAN tree (branch off main @ d1501a5). Mart + export (additive) + proposed doc-sync fold.
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (escalation), App. A.

objective: >
  Surface the team's founded year + venue (name/city/capacity) on the v2 team profile (wireframe §5
  "Founded, venue"; brief §6.2). The fields already exist in dim_team; mart_team_profile already joins
  dim_team for identity but does not pull them. Additive: add the 4 columns to the existing mart join +
  surface them in shape_team_payload's top-level identity block. Closes GAP-01.

refs: >
  #391 (un-paused, data-first) · GAP-01 (Phase B; register "pending") · CPO disposition ruling this session:
  surface the register's 4 fields — team_founded_year, venue_name, venue_city, venue_capacity (NOT
  venue_address, NOT the internal venue_api_id). backlog in .claude/active_work.md.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/**

# Structural surface (dbt_project/models/** + scripts/export_*.py) in scope -> impact_map required.
# Additive/leaf, evidenced:
impact_map: >
  writers: NO new model. mart_team_profile gains 4 identity columns from its EXISTING dim_team join
    (`teams` CTE = `select * from dim_team`, aliased `t`; mart_team_profile.sql:34-36). dim_team already
    carries team_founded_year + venue_name/venue_city/venue_capacity (dim_team.sql:13-19). No CTE change
    (select *), just +4 lines in the identity SELECT block. mart is materialized=TABLE -> full rebuild each
    run, no incremental/full-refresh dance.
  downstream: mart_team_profile is consumed by the v2 team export (scripts/export_site_data.py,
    `select * from mart_team_profile`) + documented in shared.yml. (Verify no other consumer at build.)
  layer_rules: identity columns surfaced from dim_team AT THE MART (the existing pattern — team_name/
    team_country are already done this way); the export reshapes only (top-level identity, no derivation).
    check_layer_contract; consumption-layer contract.
  deploy_order: table-materialized -> rebuilt on the next nightly run; no incremental rename, no
    --full-refresh. Export wired into NO workflow (only export_pages_data.py, the live-MVP export, runs in
    pages/ci-ui) -> zero live-MVP impact. ci-data-build builds + parses on this PR.
  blast_radius: +4 nullable identity columns on mart_team_profile (venue data is sparse — honest nulls,
    no DQ gate needed); the team payload gains top-level `founded_year` + a `venue` block. NO change to any
    existing metric/number. Live MVP (`site/`) untouched. Docs are non-executed.

decisions_taken: >
  The 4 fields (team_founded_year, venue_name, venue_city, venue_capacity) were CPO-ruled this session
  (the register's proposed disposition, approved) — venue_address (street) + venue_api_id (internal)
  excluded. Venue fields are nullable identity (sparse feed) — surfaced honestly (null/None when absent),
  no DQ test (additive identity, not a metric). Surfaced from dim_team at the mart (existing identity
  pattern); the export reshapes only.

decisions_reserved:
  - PAYLOAD SHAPE (propose at plan, CPO confirms at ExitPlanMode): top-level `founded_year` +
    a nested `venue` block `{name, city, capacity}` (None when all venue fields null — honest absence,
    mirrors the GAP-16 current_team block). Flat keys are the alternative.
  - DOC-SYNC FOLD (open governance question from #610/#611): the 02 wireframe §4/§5/§10 + register GAP-01
    row are stale (status: GAP-01 "not exported"). Whether to FOLD that doc-sync into THIS PR (per GAP-14/
    GAP-16) or ship SEPARATELY is the CPO's call at plan approval. Contract is scoped FOR the fold; if the
    CPO chooses separate, amend scope to drop the two wireframe paths (and bi-analyst routing).

done_when:
  - mart_team_profile carries team_founded_year + venue_name/venue_city/venue_capacity (from the existing
    dim_team join); shared.yml documents the 4 columns.
  - shape_team_payload emits top-level `founded_year` + a `venue` block (honest None when absent); the 4
    fields are dropped from per-season rows (added to _strip_identity); `pytest tests/test_export_site_data.py`
    green incl. new asserts.
  - (if fold) 02_team_profile.md no longer shows GAP-01 as open (§4/§5/§10) + 99_gaps_register.md GAP-01
    marked shipped.
  - `python scripts/check_layer_contract.py` passes; dbt build in ci-data-build (dbt CLI broken locally).
  - scope-auditor + analytics-engineer + cto (+ bi-analyst if docs folded) PASS (>=2 risks each); review.md
    binds the staged diff; CPO merges (never self-merge).

amendments: (none)
