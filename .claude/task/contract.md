# Task contract — A1: deserved-vs-actual into mart_team_profile

> Written on a CLEAN tree (branch feat/a1-deserved-vs-actual-team-profile off main @ 1deb5bf).
> Touches a dbt model → impact_map REQUIRED. See docs/working_agreement.md §2/§10, dbt_project/docs/layering.md.

objective: >
  Surface the deserved-vs-actual read on the v2 team page by composing the existing intermediate
  int_team_season__deserved_vs_actual (#598) into mart_team_profile (CPO-chosen backlog item A1,
  Option 1). Add deserved_rank + sot_rank_gap; one additive PR closes both "built" (mart) and "wired"
  (the v2 team export reads mart_team_profile via select *).

refs: >
  Backlog A1 + Option 1, CPO-approved this chat (2026-06-29). Plan: whimsical-swinging-mccarthy.md.
  Metrics already catalogued as rank-derived rows (#598) — no metric_catalogue change.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: mart_team_profile (changed); new upstream ref = int_team_season__deserved_vs_actual
    (intermediate, already on main since #598; grain team_sk+season_sk, matches the mart).
  downstream: `dbt list mart_team_profile+` → "football_data_pipeline.5_marts.shared.mart_team_profile"
    ONLY (leaf — no downstream models). grep `ref('mart_team_profile')` across dbt_project/models → zero
    (only doc comments in mart_player_profile/int_team_profile__yoy + the shared.yml schema entry).
    Sole consumer = scripts/export_site_data.py fetch_team_payloads (`select *` → shape_team_payload →
    _strip_identity, an identity-only denylist) → the two new metric columns auto-flow to the team payload.
  layer_rules: marts COMPOSE intermediates, never recompute (layering.md cross-layer-consumption rule).
    mart_team_profile already composes int_team_season__metrics / int_team_profile__yoy /
    int_team_profile__streaks; adding int_team_season__deserved_vs_actual is the identical pattern.
    check_layer_contract.py must stay green.
  deploy_order: mart_team_profile is materialized='table' (full rebuild each run) — additive columns,
    NO incremental schema-change / full-refresh trap. The intermediate already exists on main, so no
    upstream gap. ci-data-build builds it; the 04:00 nightly rebuilds prod. No migration ordering risk.
  blast_radius: the v2 team export gains deserved_rank + sot_rank_gap; NO existing column or number
    changes; both NULL for non-rankable league-seasons (knockouts / incomplete SoT coverage), gated
    upstream in the intermediate. RAW/other marts unaffected.

decisions_taken: >
  Rests on the CPO's Option-1 sign-off. VERIFIED (not assumed): the intermediate's actual_rank and the
  mart's existing latest_rank are the SAME value — both are int_team_season__standings_primary.standing_rank
  on (team_sk, season_sk) — so latest_rank already serves as "actual"; surface only deserved_rank +
  sot_rank_gap, no redundant actual_rank column. Formulas/metrics unchanged (already catalogued #598).

decisions_reserved:
  - How the team page renders the block (actual vs deserved bar + gap callout) — frontend, #391 paused; out of scope.

done_when:
  - mart_team_profile.sql: left join int_team_season__deserved_vs_actual on (team_sk, season_sk),
    surfacing deserved_rank + sot_rank_gap (same join shape as the streaks join).
  - shared.yml: column docs for the two new columns (null-when-not-rankable semantics; no new data tests —
    the sign/null invariants live on the intermediate).
  - `python scripts/check_layer_contract.py` green; compiled join grain-correct.
  - Export carry-through: export_site_data.py sample dry-run shows deserved_rank/sot_rank_gap in a
    seasons[] entry (NULL for a knockout/incomplete season).
  - ci-data-build green; scope-auditor + analytics-engineer PASS; CPO merges (never self-merge).

amendments: (none)
