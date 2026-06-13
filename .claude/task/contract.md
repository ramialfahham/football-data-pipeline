# Task contract — add COACHES + INJURIES to the data contract (#427)

> Audit F24: ingestion writes RAW_APIF_COACHES and RAW_APIF_INJURIES every run,
> but neither is in docs/data_contract.md — no contractual anchor for downstream
> consumers. CPO ruling 2026-06-12: file. Docs-only. See docs/working_agreement.md §2.

objective: >
  Document the two undocumented unified raw tables in docs/data_contract.md.
  Verified this session against the ingestion code:
  - RAW_APIF_COACHES — written by ingestion/api_football/loads/coaches.py via
    load_json_to_bq(raw_table("COACHES"), as_json_payload=True, append=True,
    league_code=...) → ensure_unified_raw_table. Source endpoint: /coachs (per team).
  - RAW_APIF_INJURIES — written by ingestion/api_football/loads/injuries.py via the
    same unified-append path. Source endpoint: /injuries (per league per season).
  Both are invoked in the per-competition cheap-phase run (loads/competition_runner.py
  run_cheap_phases, lines 93-96) for active competitions. They append one row per run when
  data is available, with early-return guards: coaches skips when no team_ids resolved
  (coaches.py:38), injuries skips when no season returned data (injuries.py:67). Idle/poll
  runs (run_poll_phases) do not call them. This matches how the other conditional append
  tables (transfers via load_transfers_if_enabled, standings via load_standings_if_enabled)
  already behave — so the doc rows need no per-table conditional caveat (the general skip
  pattern is already covered by the doc's "Coverage flags" + "Append-only writes" sections).
  F24's premise (these tables are written and need a contract anchor) holds.
  Both are unified raw tables with the standard schema/behaviour (see bigquery.py
  ensure_unified_raw_table): columns league_code STRING / payload JSON / ingested_at
  TIMESTAMP; WRITE_APPEND; partitioned by DATE(ingested_at); clustered by league_code;
  no merge key.
refs: #427 (audit F24).

scope_paths:
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/active_work.md   # artifact-only: handover write-out at close (amendment A2)

decisions_taken: >
  CPO-approved doc addition (audit ruling 2026-06-12: file). Pure documentation of
  EXISTING, verified pipeline behaviour — no code, schema, or pipeline change. The two
  new rows mirror the existing unified-append rows verbatim (write mode / partition /
  cluster / merge key) and the endpoints map gains /coachs and /injuries.

decisions_reserved:
  - The contract currently asserts "six tables" / "Six tables serve the entire fleet"
    (lines 3, 33) and an "additional smaller table: RAW_APIF_LEAGUES". Adding two more
    unified tables makes those counts internally inconsistent. Updating the count to
    match is REQUIRED for the doc to stay self-consistent (the whole point of F24 — a
    correct contractual anchor), not a scope expansion. If a reviewer judges the count
    wording itself a CPO-class naming/structure decision, STOP and escalate rather than
    decide the phrasing unilaterally.
  - Do NOT reclassify, re-describe, or "improve" any existing UNIFIED-RAW-TABLE row, the
    merge model, or the freshness/completeness sections — out of scope for F24. (The
    "Plan vs product" coaches/injuries fixes under amendment A1 are the exception: they
    remove a contradiction the additions create, not an unprompted improvement.)

done_when:
  - docs/data_contract.md "Unified raw tables" table has two new rows: RAW_APIF_COACHES
    and RAW_APIF_INJURIES (append / DATE(ingested_at) / league_code / no merge key).
  - the "Endpoints and raw tables" map has /coachs → RAW_APIF_COACHES and /injuries →
    RAW_APIF_INJURIES.
  - the "six tables" counts (lines 3, 33) are corrected so the prose matches the table.
  - the "Plan vs product" section is made consistent with the additions (amendment A1):
    the "Players & coaches" row no longer claims "no separate coaches ingest", and an
    "Injuries" row is added — both reflect EXISTING ingest (RAW_APIF_COACHES via /coachs,
    RAW_APIF_INJURIES via /injuries). /sidelined remains not-ingested (distinct endpoint).
  - no other section of the doc is altered; markdown still renders (tables intact).
  - reviewers: scope-auditor (always) + data-engineer-reviewer (docs/data_contract.md) — PASS.

amendments:
  - 2026-06-13 A1: scope unchanged (docs/data_contract.md already in scope_paths), but
    the edit set is extended to the "Plan vs product" section — authority: standing
    consistency rule (a doc change must not leave the doc self-contradictory; raised by
    the iteration-1 data-engineer-reviewer FAIL, which found line 161 "no separate
    'coaches only' ingest" contradicted by the new RAW_APIF_COACHES row). content: fix
    the coaches claim + add an Injuries row. Also corrected the objective's inaccurate
    "unconditionally every run" wording (early-return guards; poll-mode runs skip both).
  - 2026-06-13 A2: + .claude/active_work.md — authority: standing rule (handover kept
    current at task close; commit-exempt but not auto-editable). content: status update
    marking #427 done (PR #439).
