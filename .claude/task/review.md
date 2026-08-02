# Review — fix/547-base-tables-and-cost-guard — 2026-08-02

branch: fix/547-base-tables-and-cost-guard
diff_sha256: 1b67b65f880a9e921a8d3c22756f51745a0e7cdd1ed33b54ab293ee2be2b3ecc
# One-commit branch, so `--staged-hash` equals the cumulative `origin/main...HEAD` hash. They diverge
# on a second commit; take it from `check_task_artifacts.py --base origin/main` if one is needed.

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Authority. Round 1 correctly failed this for self-authorisation: the contract cited the layer doc's
  own "not without a documented reason" clause, and a permissive clause is not a delegation. The CPO
  ruling is now quoted verbatim and exists in `escalations.log` where claimed. The measurement is the
  documented reason the doc requires; it is not the authority, and the contract now says so.
- The instruction's scope. "Fix it and ensure that this will not happen again in the future" covers
  every item in the diff: the materialisation change, the documentation reconciliation, the pinning
  test, and the measurement script. Nothing rides on the breadth of the instruction.
- `protected_override` for `.claude/hooks/dbt_layer_gate.py` cites a separate, explicit CPO "yes" to
  that specific question, recorded in `escalations.log`. The edit is confined to what was asked
  about: the injected `2_base` string.
- Four amendments, each widening scope after a reviewer found a site. Judged as diligence rather than
  drift: every one cites CPO authority or the objective, and the builder's three failed enumeration
  claims are recorded in the contract rather than hidden.
- Threshold declarations against the diff: the reporting script is read-only and wired into nothing;
  recurring cost is declared negative WITH figures, which is the inverse of the "none from intuition"
  failure that produced this task.
- Appendix A: no rule extension without approval, no consumption shortcut, no coverage cut.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Traced the full base-layer ancestor set of `mart_team_season_insights` independently, through
  `target/manifest.json`'s `parent_map`, rather than trusting the contract's pasted `dbt ls`. It is
  exactly the nine named, and `base_apif__transfers` — the single most expensive entity at $8.56 — is
  confirmed absent from that set.
- Materialising `2_base` as tables changes no RESULT, grain or incremental behaviour. The three
  incremental core facts filter on `raw_ingested_at > max(this.raw_ingested_at)`, a value carried
  from raw, not on view-versus-table semantics; a table and a view over the same SELECT return the
  same rows within one ordered build.
- Searched `2_base` for non-determinism (`current_timestamp`, `current_date`, `rand()`,
  `generate_uuid`) that a table-freeze could alter versus a view re-evaluated per consumer. None.
- The stale-rule sites are closed: the hook and both role-brief lines now quote
  `2_base: +materialized: table`, and no contradictory claim survives outside the deliberately
  exempted historical record.
- `check_layer_contract.py` now rejects ANY per-model materialisation rather than only non-`view`,
  which is a tightening and closes the hole where the old rule would have rejected a model for
  matching the new layer default.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Both round-2 findings closed for real, verified by reading the files rather than the summary:
  `layering.md:18` and `profiles.example.yml` no longer state a materialisation at all, so the
  latter's absence from `POLICY_SITES` is now correct rather than a hole.
- The new repo-wide test fails CLOSED and is self-diagnosing: it prints the file and the matched
  text. Its coverage ceiling is real and stated — a phrasing like "2_base is a view" would evade the
  regex — but the machine-readable form is caught by the token check and no such phrasing exists in
  the tree today, verified across every `materiali[sz]` and `base…view` hit.
- `_is_bookkeeping` is not a hiding place. `.claude/task/**` is forced, because `review_input.patch`
  contains the before-text by construction. The other two exemptions are currently no-ops.
- `git ls-files` via `git -C <ROOT>` is cwd-independent under pytest, and an absent git binary makes
  the test error rather than pass, which is the correct direction for CI.
- `python-ci.yml` runs `pytest tests/` with a terminal gate that exits non-zero unless the tests
  succeed, so the new file is picked up with no registration step.
- `dbt_layer_gate.py` still fails open on every path; only the injected string changed. The
  `check_layer_contract.py` rule change is pinned by a test that loads the module and asserts on
  `materialized='view'`, so reverting it fails rather than passing silently.
- No dependency, workflow, permission or credential change anywhere in the patch.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Recurring cost, re-derived rather than accepted. Enumerated every dbt invocation in
  `.github/workflows/` independently: `dbt-scheduled.yml` and `ci-data-build.yml` are full builds
  whose tests sit inside the measured tradeoff, and `pages-match-preview.yml` is the only run that
  builds base without collapsing a test suite. It is the one declared, and its selection cannot pull
  more than the nine base models, because the other marts on that line carry no `+` prefix.
- The arithmetic. $14.20 of $29.79 is base tests re-executing the chain while base BUILDS are $0.00,
  so those collapse to one build each; the new exposure is nine builds on the second run and
  transfers is not among them. No arrangement of the figures makes the net positive. The contract
  overstates its own new cost by ignoring that those SELECTs were already inlined into the pages
  run's downstream tables, which is the safe direction to be wrong in.
- Storage as the second axis: 16 newly stored base models, cents per month against a $29.79/35-day
  query bill, and BigQuery does not bill the write.
- `protected_override` cites a real, dated, explicitly protected-path ruling, and the edit stays
  inside it.
- `scripts/report_bq_cost.py` is not a new mechanism: a read-only script in an existing tree, wired
  to nothing, adding no dependency, declared anyway.
- Guard invariants move in the safe direction. Both the hook's text and the CI check's rule are
  stricter than before, and no base model currently carries a per-model materialisation, so the
  tightened rule breaks nothing retroactively.

## escalations
(none — both CPO rulings were given directly in session and are recorded in `escalations.log` and in
`decisions_taken` / `protected_override` rather than raised as blinded questions here.)
