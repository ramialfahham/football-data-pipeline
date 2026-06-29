# Task contract — GAP-15: wire team fixtures into the v2 team payload

> Written on a CLEAN tree (branch feat/gap15-team-fixtures-export off main @ 5041396).
> Touches a consumption surface (scripts/export_*.py) → impact_map REQUIRED.
> Governing doc: the consumption-layer contract (export selects/filters/renames/strips, never derives).

objective: >
  Surface the team page's "next fixture + last 5 results per (team, season)" section (02 wireframe block 9,
  GAP-15 approved) by wiring the existing mart_team_fixtures into the v2 team export. Export-only half of
  GAP-15; the mart already precomputes everything (upcoming_rank=1 = next, recency_rank<=5 = last five,
  opponent + score + result joined from the tested int_legs__team_match leg).

refs: >
  Backlog Phase B, GAP-15 (docs/wireframes/99_gaps_register.md, approved 2026-06-11; 02_team_profile.md
  §5 block 9). CPO chose GAP-15 as the next PR this chat. Plan: whimsical-swinging-mccarthy.md.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: none (no dbt/model change). Reads the existing mart_team_fixtures (on main; grain
    (team_sk, fixture_sk); ranks precomputed).
  downstream: scripts/export_site_data.py is the leaf consumer (the v2 static export). The team payload
    teams/{id}.json gains, per seasons[] row, next_fixture (object|null) + recent_results (array<=5).
    No existing payload key changes; additive only. Consumed by the (unbuilt) v2 site_v2 frontend.
  layer_rules: consumption-layer contract — the export only selects/filters (on precomputed ranks),
    renames, nests and strips internal keys; it derives NO fact (results/ranks/opponent all come from the
    mart). check_layer_contract.py must stay green.
  deploy_order: pure export-script change; no warehouse migration. Takes effect on the next nightly export
    run post-merge. No ordering risk.
  cost: mart_team_fixtures is materialized='view' over fct_fixture (a small fact — one row per fixture),
    so there is no stored table to cluster; the new query is ONE bounded scan per nightly export, filtered
    on the precomputed ranks (post-window, so no further partition pruning, but the underlying fct_fixture
    scan is small and fixed). Not a per-team N+1 (one query for the whole run). Zero API-Football quota
    impact — BigQuery bytes only, on the existing daily export path; no new run added.
  blast_radius: the team payload only; the per-fixture deep-link / fixture URL identity is DEFERRED to
    GAP-19 (the mart deliberately omits it) — GAP-15 ships display rows only.

decisions_taken: >
  Rests on the CPO's GAP-15 pick + the 02 wireframe binding (block 9). Shape mirrors the existing player
  two-mart pattern (fetch_player_payloads / shape_player_payload(profile_rows, match_rows)). Display fields
  only; internal keys (team_sk, fixture_sk, opponent_team_sk, ranks) stripped per existing discipline.
  Published-payload key names — next_fixture (object|null) + recent_results (array<=5), nested per
  seasons[] row — are CPO-DECIDED (§10 naming): surfaced in the approved plan and confirmed by an explicit
  AskUserQuestion sign-off this chat (2026-06-29). Permanent once published; recorded here, not reserved.

decisions_reserved:
  - The per-fixture deep-link (fixture URL identity) — GAP-19 item 5, NOT in scope here.
  - Block-5 deserved-vs-actual wireframe staleness (binds to ratio-space performance_vs_results_gap; A1
    shipped rank-space deserved_rank/sot_rank_gap) — FLAGGED separately, not this PR.

done_when:
  - fetch_team_payloads queries mart_team_fixtures (where upcoming_rank=1 or recency_rank<=5; sample-scoped)
    + groups by team_sk; shape_team_payload(profile_rows, fixture_rows) attaches next_fixture +
    recent_results per seasons[] row, display fields only, internal keys stripped.
  - tests/test_export_site_data.py updated for the 2-arg signature + asserts attachment/order/empty-case.
  - `python -m pytest tests/test_export_site_data.py` green; `python scripts/check_layer_contract.py` green.
  - scope-auditor + analytics-engineer + cto PASS; CPO merges (never self-merge).

amendments: (none)
