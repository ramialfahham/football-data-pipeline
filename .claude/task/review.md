# Review — docs/data-contract-coaches-injuries — 2026-06-13

> Issue #427 (audit F24): document RAW_APIF_COACHES + RAW_APIF_INJURIES in
> docs/data_contract.md. Docs-only. Required reviewers for docs/data_contract.md:
> scope-auditor + data-engineer-reviewer. Two cold blinded iterations:
> iteration-1 data-engineer-reviewer FAIL (the additions left "Plan vs product"
> line 161 — "no separate 'coaches only' ingest" — self-contradictory; the
> contract's "unconditionally every run" wording was also inaccurate). Resolved
> via amendment A1: fixed the coaches line + added an Injuries row, and corrected
> the contract's invocation wording (early-return guards; poll-mode runs skip both).
> Iteration-2: both reviewers PASS against the hash below.

diff_sha256: 799e12b34aa6088e36ace9ad5c0742575318169dd5a6824bf05134894879611f

## scope-auditor
VERDICT: PASS
risks_checked:
- Schema/write-mode attestation: verified coaches.py:64 + injuries.py:74 both call
  load_json_to_bq(as_json_payload=True, append=True, league_code=...) → ensure_unified_raw_table
  (bigquery.py:166), which creates exactly the declared schema (league_code STRING /
  payload JSON / ingested_at TIMESTAMP), partition DATE(ingested_at), cluster league_code,
  no merge key — the two new rows match the code, not invented attributes.
- Internal doc coherence: confirmed "six"→"eight" applied at both prose sites (lines 3, 33)
  and the unified table now has 8 rows; no remaining statement contradicts the existence of
  the two tables (the Plan-vs-product coaches line is fixed, /sidelined correctly stays
  "not ingested" as a distinct endpoint); the Plan-vs-product edits are consistency fixes
  flowing from the additions, not a smuggled §10 editorial/naming decision; only the two
  declared scope_paths touched, no protected path.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Write-path correctness: coaches.py:64 and injuries.py:74 both route through
  ensure_unified_raw_table producing WRITE_APPEND / partition DATE(ingested_at) /
  cluster league_code / no merge key — the doc rows claim exactly this; no WRITE_TRUNCATE
  risk. Both merge their fan-out (coaches: all teams; injuries: all seasons) into one
  appended row per run per competition.
- Invocation accuracy + poll-mode: verified both are called only in run_cheap_phases
  (competition_runner.py:93-96), not run_poll_phases; early-return guards confirmed at the
  exact cited lines (coaches.py:38 no team_ids; injuries.py:67 no merged data). Leaving the
  doc rows caveat-free is consistent with the conditional transfers/standings rows.
- Count + /sidelined: eight unified rows match the "eight tables" prose; RAW_APIF_LEAGUES
  stays the separate "additional" table; the new Plan-vs-product coaches/injuries entries
  are correct and /sidelined (distinct endpoint) correctly remains "not ingested".

## escalations
(none — iteration-1 FAIL resolved by amendment A1 consistency fixes + contract wording
correction; both reviewers PASS in iteration-2. Two PRE-EXISTING staleness items the
data-engineer noted are out of F24 scope and flagged as a follow-up: the Landing Zone
"verbatim envelope" line vs coaches.py's wrapped dict, and the "Append-only writes" prose
list not enumerating coaches/injuries.)
