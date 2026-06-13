# Review — docs/data-contract-followups-427 — 2026-06-13

> #427 review follow-up: fix two pre-existing data_contract.md inaccuracies (the
> "verbatim envelope" Landing-zone wording; the append-only prose missing coaches/injuries).
> Within the CPO standing autonomous-backlog grant (escalations.log 2026-06-13). Docs-only,
> non-protected. Required reviewers: scope-auditor + data-engineer-reviewer (docs/data_contract.md).
> Three cold iterations: iter-1 data-eng FAIL (the squads/players reshape was unacknowledged),
> iter-2 data-eng FAIL (the fix then contradicted line 23 "Nothing is discarded"); both fixed
> (merge-vs-reshape split named for players/squads + coaches; line 23 scoped to response data;
> contract done_when corrected). iter-3: both PASS against the hash below.

diff_sha256: 379a079f8ec2ad3a6f78e3a8590f52bb40e1e39a6af68c3f4e8673cbde4e2cd1

## scope-auditor
VERDICT: PASS
risks_checked:
- Authorization + §10: the task is a #427 doc follow-up explicitly covered by the recorded
  standing autonomous-backlog grant (escalations.log 2026-06-13); changes describe EXISTING
  loader behaviour (correcting an inaccurate doc), not a product/metric/naming/mechanism
  decision — no §10. Only non-protected paths; no protected path touched.
- Scope + internal consistency: only the flagged areas of data_contract.md changed
  (Landing-zone note, payload column, line 23, append prose) + the contract's own done_when
  correction; the unified-tables table and merge model are untouched. The Landing-zone note,
  payload column, line 23, and append list are mutually consistent (merge vs players/squads+coaches
  reshape; response data kept, envelope metadata dropped; append list matches the table).

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Loader-faithfulness: verified against the code — RESHAPE loaders coaches.py
  (`{league_code, response:[{team_id, coach}]}`) and squads.py
  (`{league_code, response:[{team_id, season, players_payload}]}`) store no envelope metadata;
  MERGE loaders fixtures/standings/teams/injuries concatenate responses into a standard envelope
  recomputing results/paging (injuries correctly classified as MERGE). The note's structures
  match the actual payloads.
- Line 23 consistency + append accuracy: the old absolute "Nothing is discarded" is replaced by
  "No `response` data is discarded… reshape loaders drop only the per-call envelope metadata,
  not the response items" — factually correct and no longer contradicting the reshape note. The
  append-only prose now lists fixtures-next/standings/teams/players/coaches/injuries/leagues,
  matching the unified-raw-tables table (all WRITE_APPEND). Pre-existing out-of-scope note: teams.py
  also injects a per-item `league` block (a separate undocumented detail, predates this patch).

## escalations
(none — iter-1/iter-2 data-engineer FAILs (squads reshape omission; line-23 contradiction) fixed
in-cycle; both PASS in iter-3. Pre-existing teams.py league-injection doc gap flagged as a future
follow-up, out of this task's scope.)
