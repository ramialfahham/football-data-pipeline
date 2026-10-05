# Review — fix/bl1-soft-completeness-gate — the Bundesliga's completeness gate is soft like every other competition

diff_sha256: 7de647d56a60532c3e3ba5b9d9149db7d72877c251e8f1be7a235dce6c638112

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the registry, the contract and excluded task and tracker files only, all in scope_paths; no amendment.
- The one added line sets BL1's gate to soft; all 48 registry entries are now soft, none hard, matching the contract's count.
- Section 10: an application of the CPO's quoted words of 2026-10-05; no metric, name, URL, mechanism or cost; the code default is reserved and untouched.
- No impact map needed (no structural path); no secret, workflow or escalations.log change; no other document describes the gate.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Registry: 48 entries, 48 gate lines, none hard; BL1's value in the same unquoted format; no other key changed (provider ids, history_seasons, ingest_active untouched).
- registry.py accepts soft; only an active entry without the key defaults to hard, and none is left.
- The gate is not projected into dbt_project.yml or the seed; sync_dbt_vars has nothing to write.
- completeness.py treats soft as report-only: a BL1 gap is still reported and no longer fails the run.
- The only test naming a BL1 hard gate reads a synthetic league block, not the registry; no registry test pins BL1's gate.

## escalations
(none)
