# Task contract — squad `/players` fetch-side skip (stop nightly quota bleed)

> Written on a CLEAN tree (branch `fix/ingest-squads-skip-cached` off main). CPO approved
> the plan this session (2026-07-06): squads-only fetch-side skip + doc + skill checklist.
> See plan `C:\Users\Rami\.claude\plans\logical-moseying-noodle.md`.

objective: >
  The nightly `squad` phase re-fetches `/players` for every team × every history season across
  all in-season competitions EVERY run (~2h22m, ~50% of the daily API quota), because
  `squads.py` has storage-side merge but NO fetch-side skip. Give it the same skip the sibling
  endpoints already have (fixtures `read_coverage`, per-player `players_needing`, squad-catchup
  `captured_team_seasons`): fetch only the current (reference) season always + any un-captured
  historical `(team, season)`; skip finished team-seasons already in RAW_APIF_PLAYERS (immutable).
  Then document the invariant and add it to the onboard-endpoint checklist so it stops being
  memory-dependent.
refs: plan logical-moseying-noodle.md; CPO plan approval 2026-07-06; sibling pattern in
  loads/player_squads.py (captured_team_seasons + select_squad_catchup_team_ids).

scope_paths:
  - ingestion/api_football/loads/squads.py
  - ingestion/api_football/loads/competition_runner.py
  - tests/test_squad_players_rows.py
  - docs/data_contract.md
  - .claude/skills/onboard-endpoint/SKILL.md
  - .claude/task/**

impact_map: >
  writers: loads/squads.py is the sole writer of RAW_APIF_PLAYERS (one row per (team, season),
    merge-on-write via _delete_superseded_player_rows). This change alters ONLY which (team,
    season) keys are fetched from the API — the row shape, the write path, and the merge/delete
    are untouched.
  downstream (grep, no dbt file changed): RAW_APIF_PLAYERS -> stg_apif__players ->
    base_apif__players + base_apif__player_team_season -> 3_core (dim_player,
    dim_player_team_season_mapping) -> marts (mart_roster, leaderboards/benchmarks). dbt CLI is
    broken locally; no model/SELECT/ref() change here, so lineage is unchanged by construction.
  layer_rules: none — ingestion Python only; no dbt model or layer touched; check_layer_contract
    unaffected.
  deploy_order: no warehouse migration. Pure ingestion behaviour; takes effect on the next
    scheduled/CI ingest, no --full-refresh or model rebuild needed. Safe to merge anytime.
  blast_radius: DATA-EQUIVALENT / none. A finished season's /players response is immutable, so
    not re-downloading it yields byte-identical downstream data while removing ~all historical
    /players calls; steady state = current-season re-fetch only. A brand-new team or an
    un-captured historical (team, season) is still fetched (backfill/gap-heal intact). RAW row
    count only ever grows or holds, never shrinks.

decisions_taken: >
  Rests on the CPO's plan approval this session: (1) fix squads only; (2) finished-vs-live split
  — always re-fetch the reference season (per-season stats accumulate), skip captured historical
  seasons — mirroring the established fixtures/details and player_squads-catchup treatment of
  finished data; (3) prevent recurrence via a documented invariant + onboard-endpoint checklist,
  not a CI guard.

decisions_reserved:
  - transfers.py has the same class of re-fetch gap (cheaper: 1 call/team, no ×season×pages) —
    deferred to its own PR (CPO, this session). Not touched here.
  - Provider retroactive edits to a FINISHED season would not be re-pulled (accepted trade-off;
    a periodic full refresh via API_FOOTBALL_INGEST_FORCE_FULL / a manual run remains available).
  - A machine-enforced guard for the invariant was explicitly deferred in favour of doc + skill.

done_when:
  - squads.py fetches only (reference season × teams) + un-captured historical (team, season),
    via a pure planner + a BQ coverage reader; emits `phase=squad /players to_fetch=N
    skipped_cached=M` (fixtures-style).
  - `pytest tests/test_squad_players_rows.py tests/test_player_squads_catchup.py` passes
    (existing loader tests updated for the new reader; new pure-planner + reader tests added).
  - validate-local gates pass (ruff/black/flake8, import checks).
  - docs/data_contract.md states the fetch-side-skip invariant; onboard-endpoint SKILL.md carries
    the checklist item.
  - scope-auditor + data-engineer-reviewer + cto-reviewer PASS (>=2 risks each); review.md
    diff_sha256 binds; CPO merges.

amendments: (none)
