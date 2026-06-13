# Task contract — drop the BL1 hardcode in base_apif__transfers (#420)

> Audit F1/F2: base_apif__transfers.sql:3 has `where ... league_code = 'BL1'` — a
> hardcoded competition identifier in a 2_base model, violating the competition-agnostic
> rule (CLAUDE.md: league_code never hardcoded in business logic; zero-file rule).
> CPO ruling 2026-06-12: file. REAL behaviour change — verify DQ. See docs/working_agreement.md §2.

objective: >
  Make base_apif__transfers competition-agnostic by removing the `and league_code = 'BL1'`
  filter (keeping only the `player_id is not null` data-presence guard), and update the
  now-stale "BL1 only for now" comment in base_apif__players. Investigation this session:
  - Transfers are ingested for EVERY competition (loads/transfers.py is gated only by the
    global API_FOOTBALL_FETCH_TRANSFERS env flag, called for all leagues in
    competition_runner.py), so the BL1 filter is actively dropping real data from every
    other league — this is a genuine behaviour change, not a no-op.
  - stg_apif__transfers is already competition-agnostic (reads all league_codes from the
    unified raw table) and already drops null transfer_date.
  - base_apif__players transfers_src ALREADY has no league filter (reads all of
    base_apif__transfers with `player_id is not null`); it was implicitly BL1-only only
    because the base was. So players needs ONLY the comment fix, no logic change.
  - Consumers of base_apif__transfers: base_apif__players (player-identity fallback) and
    fct_transfer (leaf core fact — NO mart/export consumers). No UI/shipped-number impact.
refs: #420 (audit F1/F2).

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__transfers.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - .claude/task/contract.md
  - .claude/active_work.md   # artifact-only: handover write-out at close (amendment A1)

decisions_taken: >
  CPO-approved fix (audit ruling 2026-06-12: file). Replace the league_code='BL1' filter
  with the data-presence guard only, per the issue's stated fix. Competition-agnostic is
  the non-negotiable architecture rule (CLAUDE.md), so making the base model agnostic is
  the codified-correct change, not a judgement call.

decisions_reserved:
  - DQ verification is the real gate and runs in ci-data-build (full dbt build + tests),
    not locally (Tier-3 BQ build is CI-only). Expected to hold by construction:
    * fct_transfer.player_sk → dim_player (not_null + relationships, ERROR severity): every
      transfer player flows into base_apif__players via the same base_apif__transfers, so
      it is guaranteed present in dim_player — the change keeps fct and the player fallback
      in lockstep across all leagues.
    * fct_transfer from/to_team_sk → dim_team are severity:warn + where ...is not null —
      foreign-league teams not in dim_team are by-design nulls; more leagues = more warns,
      not failures.
    * base_apif__transfers not_null(league_code/player_id/transfer_date) + unique grain:
      staging guards transfer_date, base guards player_id, qualify guarantees the grain.
    If ci-data-build surfaces a NEW hard DQ failure (e.g. an ERROR-severity relationship
    breaks for a non-BL1 league), STOP and escalate — do not silently re-add a league
    filter or downgrade a test severity.

done_when:
  - base_apif__transfers.sql: the filter is `where player_id is not null` only (no league_code='BL1').
  - base_apif__players.sql: the transfers_src comment no longer says "BL1 only for now";
    it states the fallback now covers all leagues via the competition-agnostic base.
  - no other model changed; grep shows zero remaining `league_code = 'BL1'` (or any
    hardcoded league_code) in dbt_project/models/2_base/.
  - validate-local Tier 1+2 green (dbt parse, sqlfluff lint); full DQ build deferred to
    ci-data-build (the authoritative gate for this change).
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**) — PASS.

amendments:
  - 2026-06-13 A1: + .claude/active_work.md — authority: standing rule (handover kept
    current at task close; commit-exempt but not auto-editable). content: status update
    marking #420 done (PR #441).
