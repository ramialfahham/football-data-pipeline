# Task contract — test: restore the fct_fixture FK guard (PR2 of 2 — the alarm)

> The idle-mode completeness bug (PR1 #514) ran silently because the referential-integrity tests that
> would have caught it — every fanout fixture must have a fct_fixture header — were DELIBERATELY SUPPRESSED
> in core.yml ("No FK test: fct_fixture covers current-season snapshots only"), with the thin state written
> into the column descriptions as if intended. PR2 RESTORES those three FK tests and corrects the
> descriptions. It is the durable guard so this can never silently regress again. Unblocked now that PR1 +
> the zero-API recovery made fct_fixture consistent with the fanout facts (verified: 0 orphans warehouse-wide).
> Design + 2-PR split CPO-approved this conversation 2026-06-19. See working_agreement.md §2/§10/Appendix A.

objective: >
  In dbt_project/models/3_core/core.yml, add the `relationships` test (fixture_sk -> ref('fct_fixture'),
  field fixture_sk) to the fixture_sk column of fct_fixture_player_stats, fct_fixture_team_stats, and
  fct_fixture_event, and replace each misleading description ("No FK test: fct_fixture covers current-season
  snapshots only; this incremental table accumulates historical seasons.") with one that states the FK and
  the now-correct invariant (fct_fixture carries full history via the append-complete-snapshot carry-forward
  from PR #514). No other change.

refs: >
  This conversation 2026-06-19. PR1 #514 (merged) fixed the idle-mode snapshot thinning; the one-time
  zero-API recovery rebuilt fct_fixture from RAW history (0 orphans verified). The suppressed tests are
  core.yml lines ~593/543/676. This is the deferred PR2 alarm from #514's contract.

scope_paths:
  - dbt_project/models/3_core/core.yml
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO directed PR2 this conversation ("PR2 now"). The FK tests were deliberately suppressed to mask the
  idle-mode thinning (Appendix-A "disabled the failing test" anti-pattern); restoring them is the principled
  un-masking. The relationships test is the standard dbt referential-integrity guard. Severity = error
  (hard-fail) — DQ is non-negotiable. The data is now consistent (0 orphans), so the tests pass.

decisions_reserved:
  - Exact test form: the standard `relationships` test (fanout fixture_sk -> fct_fixture) is chosen, as it
    directly encodes "every fanout fixture has a header". If the analytics-engineer prefers a different/
    additional form (e.g. a registry-depth completeness test), that is a build-detail call for that reviewer.
  - This PR adds no data and no ingestion/mart change; it is core.yml schema tests + descriptions only.

done_when:
  - core.yml: the fixture_sk column of fct_fixture_player_stats / _team_stats / _event each carries
    `relationships: { to: ref('fct_fixture'), field: fixture_sk }` (in addition to not_null), and the
    "No FK test ... current-season snapshots only" description is replaced with the FK + carry-forward wording.
  - dbt parse succeeds; `dbt test --select fct_fixture_player_stats fct_fixture_team_stats fct_fixture_event`
    (the restored relationship tests) PASS against the current warehouse (0 orphans).
  - validate-local passes (sqlfluff/dbt parse offline gates).
  - Commit on branch test/fct-fixture-fk-guard; post-commit opens the PR.
  - reviewers: scope-auditor + analytics-engineer-reviewer PASS (each >=2 named risks); no FAIL; no ESCALATE.

amendments: (none)
