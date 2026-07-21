# Review — docs/task0-metric-layer-tests — 2026-07-21

> Blinded review of the TASK 0 redefinition (values + machine gates). One required reviewer per
> `.claude/review_routing.json`: scope-auditor (always). No code path is touched, and `contract.md` sits on
> `artifact_only_never`, so this commit is NOT review-exempt. PASS, first round.

diff_sha256: e78cbcb8affe9750eb7dd560b2753fd8fe4c460b432bb50ef61acdd1f0427a0b

## scope-auditor
VERDICT: PASS
risks_checked:
- Every factual claim re-derived from the repo rather than trusted — confirmed `assert_team_metric_meaning_complete.sql` really does carry the `entity in ('team','team and player')` predicate that let the player gap go unnoticed; confirmed all five named metric-layer tests exist in `dbt_project/tests/`; confirmed exactly 4 seed rows contradict themselves (`cards_yellow`, `cards_red`, `cards_total`, `shots_on_goal_against`, all `entity=player`, all `lower_is_better=false` beside `direction=lower_better`); and confirmed `scripts/export_metric_definitions_json.py` genuinely reads `lower_is_better`, which is what makes changing it a live-behaviour change rather than a mechanical tidy.
- Specification-not-implementation boundary — this task must define the gates without building them. Verified only `.claude/active_work.md` and `.claude/task/contract.md` changed, and that no test, seed, dbt model, export script or `site_v2` file was written.
- Test-widening fidelity (step b) — the load-bearing fix is REMOVING the entity predicate, and a careless implementer could keep it and defeat the whole gate. Judged mitigated: the handover states it explicitly ("Drop the entity predicate so the test fails if ANY row has an empty..."), the test's own docstring already anticipates broadening, and the required rename signals the change.
- Test-sequencing discipline (step c) — the lockstep test cannot pass until the 4 contradictions are fixed, so adding it early would produce a red build and invite weakening it to get green. Judged mitigated: the handover warns to "land the fix and the test together" and FIRST STEPS repeats "Do all three steps, in this order".
- Decision integrity on `lower_is_better` — confirmed the resolution is presented as an open CPO decision with both options and their trade-offs, and is not quietly pre-decided, which matters because one option moves live MVP behaviour.
- Internal consistency of the TASK 0 definition — confirmed the roadmap line, the TASK 0 heading, the TASK 0 body and FIRST STEPS all now describe TASK 0 as values PLUS tests, with no leftover text implying it is only the 28 values.

## escalations
(none)
