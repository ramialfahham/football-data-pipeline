# Task contract — PR-i: transfers chain rebuild (player-data initiative)

> APPROVED player-data plan (C:\Users\Rami\.claude\plans\player_data_ingestion_plan.md §2/§4/§5/§8)
> + CPO rulings (escalations.log 2026-06-14): reinstate the retired transfers chain (#420) as the
> dated source for affiliation order. Cost APPROVED (by-team axis; ~930–3,000 backfill,
> ~130–430/day ongoing). History depth = FULL (all current teams). This is PR-i: ingestion →
> RAW_APIF_TRANSFERS → staging → base (dedup) → `fct_transfer` (dated moves fact). The affiliation
> TIMELINE (int_player_affiliation_timeline) + current-team derivation are LATER PRs, NOT here.
> Built following the new `onboard-endpoint` skill (Steps 0–4 already satisfied this session).
> See docs/working_agreement.md §2/§5/§6/§10, docs/data_contract.md, docs/agent_guardrails.md.

objective: >
  Rebuild the transfers ingestion chain end-to-end:
  (1) Ingestion: a `loads/transfers.py` module (mirror `loads/squads.py`) that pulls
      `/transfers?team={id}` for every team (by-team axis — one call returns all of a team's
      players' moves) and appends to the unified raw table; a `transfers_response_for_team`
      helper in `fixture_scheduling.py` (mirror `players_response_for_team`); a
      `run_transfers_for_competition` in `loads/competition_runner.py`; wired into
      `orchestrator.py` right after `run_squads_for_competition`. Respects the ingest lock +
      daily quota (quota-exhaustion break, per-team try/except), with an
      `API_FOOTBALL_SKIP_TRANSFERS` env skip mirroring `API_FOOTBALL_SKIP_PLAYERS`.
  (2) Raw: `RAW_APIF_TRANSFERS` is created by `load_json_to_bq(..., as_json_payload=True,
      append=True, league_code=...)` (unified {league_code, payload, ingested_at} — no manual DDL).
  (3) Staging: `stg_apif__transfers` (raw cleanup only) unpacking the payload to one row per
      raw move: player_id, transfer_date, type (raw string), team_in_id, team_out_id,
      league_code, raw_ingested_at. Source `raw_apif_transfers` declared in `sources.yml`.
  (4) Base: `base_apif__transfers` — dedup the provider's duplicate move-records (same
      player/team_in/team_out, near-identical date — e.g. the Barkok double-Schalke case) to one
      row per distinct move; keep the raw `type` string.
  (5) Core: `fct_transfer` — the dated moves fact. Grain: one row per distinct
      (player, team_out, team_in, transfer_date) move, surrogate-keyed; tested unique + not-null
      on the keys. Latest-season dim resolution (league_sk/season_sk) is NOT required here —
      this is the move event, not a season rollup.

refs: player-data plan §2/§4/§5/§8; escalations.log 2026-06-14 (transfers reinstated + cost
  approved + history=all); onboard-endpoint skill; loads/squads.py + players_response_for_team
  (the mirrored patterns).

scope_paths:
  - ingestion/api_football/loads/transfers.py
  - ingestion/api_football/fixture_scheduling.py
  - ingestion/api_football/loads/competition_runner.py
  - ingestion/api_football/orchestrator.py
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/1_staging/api_football/stg_apif__transfers.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__transfers.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_transfer.sql
  - dbt_project/models/3_core/core.yml
  - docs/data_contract.md
  - .claude/task/contract.md

decisions_taken: >
  Reinstating transfers + its by-team ingest cost is CPO-APPROVED (escalations.log 2026-06-14;
  reverses #420). History depth = all current teams (CPO-decided). Transfers rides the EXISTING
  04:00 run via the orchestrator (no new run cadence). By-team axis (one call per team returns all
  its moves — verified live: Bayern = 289 players in one call). Base dedups the provider's
  duplicate move-records; `fct_transfer` grain = one distinct move per (player, team_out, team_in,
  date). The raw `/transfers` `type` field is kept as the raw string in this PR.

decisions_reserved:
  - The affiliation TIMELINE (`int_player_affiliation_timeline`, valid_from/to + sequence) and the
    current-team derivation are NOT in this PR — they are a later core/intermediate PR. PR-i stops
    at `fct_transfer` (the dated-moves fact).
  - Do NOT invent a canonical transfer-`type` taxonomy (loan/permanent/free/…) — the provider enum
    is messy (N/A, Free, Loan, Back from Loan, Transfer, None, fees). Keep the raw string; any
    normalized type vocabulary is a §10 metric/label decision — surface it, don't decide.
  - Dedup KEY is EXACT (player_id, team_in_id, team_out_id, transfer_date) — this removes the
    by-team cross-query duplicates (the dominant, certain duplicate source) and the provider's
    exact-duplicate rows, WITHOUT merging genuinely-distinct moves (e.g. a player who left and
    re-joined a club on different dates stays two rows). Provider NEAR-duplicates with differing
    dates (e.g. the same move recorded 2 days apart under different `type`s) are deliberately NOT
    fuzzy-merged here — a date-window heuristic risks collapsing real moves; that refinement, if
    ever wanted, is a separate decision. (data-cleaning, agent-executable)
  - No new run cadence; no extra schedule; no protected-guard edit (none in scope).

done_when:
  - `loads/transfers.py` + `transfers_response_for_team` + `run_transfers_for_competition` exist
    and `orchestrator.py` invokes it after squads; `python -m py_compile` clean on changed Python;
    the ingestion respects the quota break + SKIP env.
  - `stg_apif__transfers` / `base_apif__transfers` / `fct_transfer` build; `raw_apif_transfers`
    source declared; `fct_transfer` has a tested unique grain + not-null keys; base dedup tested.
  - `dbt parse` resolves all refs; sqlfluff clean on changed SQL; validate-local gates
    (layer contract, registry sync, python) pass.
  - reviewers: scope-auditor (always) + data-engineer-reviewer (ingestion/**) +
    analytics-engineer-reviewer (dbt_project/**) — PASS.

amendments:
  - 2026-06-14: dedup key = EXACT (player, team_in, team_out, transfer_date), in the BASE layer
    (staging does no dedup; core reads the deduped base). Removes the by-team cross-query duplicate
    (each move fetched twice, once per involved club) + exact provider duplicates, WITHOUT
    fuzzy-merging near-duplicate-date records (date-window merge could fuse genuine repeat moves).
    Authority: CPO RULING (escalations.log 2026-06-14 feat/transfers-chain, "do it") — the
    iteration-3 scope-auditor flagged that "which records are the same move" is a CPO data-modeling
    decision, not builder self-classification; the CPO confirmed the exact-key dedup and its base-
    layer home. content: decisions_taken (cross-query note) + decisions_reserved (exact dedup key).
  - 2026-06-14: + docs/data_contract.md to scope_paths. Authority: required doc-sync (iteration-1
    scope-auditor + data-engineer FAIL) — data_contract.md explicitly documents RAW_APIF_TRANSFERS
    as RETIRED; reinstating the chain MUST un-retire it there (add to the unified raw-table list,
    update the retired/transfers notes). Clean-tree amendment (code stashed). content: un-retire
    transfers in data_contract.md.
