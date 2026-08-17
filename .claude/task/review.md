# Review — fix/75c-event-consistency-tests — 2026-08-17

diff_sha256: 20af9490d83e9ba7abdab975e9d195e59fb16bd60d6409ce814e3e8ca6e2b287

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Diff file set vs `scope_paths`: the new singular test, `dbt_project.yml` (one var), `contract.md`, `escalations.log`. No model, no seed, no mart, no ingestion file — this adds an assertion and nothing else.
- The task was reduced, not expanded, against the plan the CPO approved: three designed tests became ONE, because two died against prod data. Both rejections are recorded with their measured reasons rather than dropped silently.
- `decisions_reserved` does not launder anything: the 5 damaged fixtures are explicitly NOT repaired here, and the "may a complete-but-smaller response supersede" question stays with the CPO (#896 rules it the other way today).
- The var is config-as-code and carries an explicit "never raise this to make a build green" warning, so the one way to abuse it is named in the file that holds it.
- Credential sweep of the diff: none.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 FAILED and the finding was real: the scope CTE grouped `max(raw_ingested_at)` over `base_apif__fixture_events` itself, so a fixture losing ALL its events produced no CTE row and the inner join dropped it — the TOTAL-loss case, undetectable at any cutoff, forever. Measurement could not have caught it, because the known incident was PARTIAL for all 5 fixtures; it was found by reading the join.
- ROUND 2 FIX TRACED END TO END: `in_scope` now reads `fct_fixture`, independent of base. A fixture that loses every event keeps its `fct_fixture` header row, stays in scope, and all of its accumulated fact rows flag. The dependency on base surviving is gone.
- `fct_fixture` verified as the scope source rather than assumed: `fixture_sk` not_null+unique, `fixture_date` not_null, and upstream `loads/fixtures.py:185-197` refuses to write an empty fetch while 206-236 carry forward unrefreshed seasons — so the header row is genuinely always present.
- NEW BLIND SPOT NAMED AND ACCEPTED: a fixture kicking off before the cutoff but damaged after it is permanently out of scope. That is precisely the CPO's "scope it to new data" instruction, and it is disclosed in matching language in three places (test header, contract impact_map, escalations.log).
- Direction: the query is driven FROM the fact, so only fact>base can produce a row; incremental lag (base ahead) structurally cannot fail. Join keys are the models' declared, tested grains; no NULL-comparison hazard.
- Omitting `league_code` from the anti-join is safe — `fixture_sk`/`fixture_id` is globally unique in API-Football and both sides are int64.
- Var placement sits outside the `sync_dbt_vars.py`-generated block; `check_registry_var_sync.py` passes.
- Layer rules: a leaf singular test, no model/grain/materialisation change.

## escalations
- question: May a COMPLETE provider response carrying strictly less data than what is stored supersede it?
  CPO ANSWER: NOT TAKEN — still open, and deliberately so. This test makes the loss VISIBLE; it does not decide who wins. #896 rules the ambiguous case the other way today (2026-08-03), so changing it reverses part of that ruling. Recorded in `escalations.log` and `decisions_reserved`.
