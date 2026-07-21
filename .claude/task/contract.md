# Task contract — make TASK 0 close the metric layer with TESTS, not just values

> Written on a CLEAN tree (branch `docs/task0-metric-layer-tests` off main @ 1592357).
> CPO-directed 2026-07-21: *"We need proper tests for the metric layer as well so there are no sudden gaps
> or surprising ambiguities."* Said in the same breath as a standing criticism worth recording verbatim,
> because it is the reason this task exists at all: *"The problem is that it happens frequently and you're
> always saying something like 'writing it down' but it doesn't improve your behaviour. It will happen
> again and then you are writing down again to dead documents without impact."*
> Bookkeeping/handover refresh → plan mode SKIPPED by standing rule (2026-06-30); contract + review +
> commit gate still apply. See [[feedback-handover-discipline]] [[feedback-metric-catalogue-governance]].

objective: >
  Rewrite TASK 0 in `.claude/active_work.md` so that "finish the metric layer" means **fill the 28 missing
  `interpretation` values AND install the machine gates that make the gap un-reintroducible** — not just
  write 28 sentences. The CPO's point is that a memory note or a handover paragraph has no enforcement, so
  the same class of gap recurs; a dbt test fails the build regardless of what anyone remembers.
  Two concrete gates are specified, with their sequencing, because each can only pass after a
  corresponding data fix:
  (T1) The existing meaning-completeness test is TEAM-SCOPED — which is precisely why 28 player rows sat
       empty and nothing complained. Widen it to every entity, after the 28 are filled.
  (T2) NOTHING currently checks that `lower_is_better` and `direction` agree. They contradict each other on
       4 rows today. Two columns asserting different things about the same metric is the "surprising
       ambiguity" the CPO named. Resolve the 4, then add the lockstep test.
  This contract does NOT write the values or the tests — it makes the handover specify them correctly so a
  fresh chat executes the whole job rather than half of it.

refs: >
  Verified live this session: `dbt_project/tests/` contains 5 metric-layer tests
  (`assert_metric_catalogue_expr_resolvable`, `assert_metric_catalogue_unique_by_entity`,
  `assert_no_uncatalogued_season_metric`, `assert_team_metric_meaning_complete`,
  `assert_mart_team_season_insights_metric_consistency`) · the 4 `lower_is_better`/`direction` divergences
  (`cards_yellow`, `cards_red`, `cards_total`, `shots_on_goal_against`) were found and logged during #677
  and are still unresolved on main · issue **#530** already tracks widening catalogue-first traceability
  beyond the two season models.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: none. Handover DOCUMENT only. No seed, dbt model, test, export or `site_v2` change; zero rows,
    zero numbers, zero runtime behaviour. The tests themselves are written by the NEXT task, not this one.
  downstream: `.claude/active_work.md` is fed to every fresh chat by the `handover_in` SessionStart hook.
    Getting TASK 0's definition right here is what determines whether the next session installs the gates
    or just fills cells and declares victory — the exact failure the CPO is objecting to.
  layer_rules: documentation only.
  deploy_order: nothing to deploy.
  blast_radius: zero runtime impact.

decisions_taken: >
  1. TASK 0 is redefined as THREE steps in a required order: (a) fill the 28 `interpretation` values;
     (b) widen the meaning-completeness test from team-only to every entity; (c) resolve the 4
     `lower_is_better`/`direction` contradictions and add a lockstep test. Step (b) cannot pass before (a),
     and (c)'s test cannot pass before (c)'s data fix — the handover states that sequencing explicitly so a
     fresh chat does not add a test that fails on arrival and then weaken it to get green.
  2. The `lower_is_better` resolution is flagged as a REAL CPO decision, not a mechanical fix: that column
     is what the LIVE MVP export reads, so changing it moves live behaviour. The handover records both
     options (change the boolean vs change the direction) rather than presuming one.
  3. The rationale is recorded in the handover in the CPO's own terms — enforcement over intention — so the
     next chat understands WHY the tests are part of the task and does not drop them as optional polish.
  4. Issue #530 is referenced as the broader traceability gate rather than pulled into TASK 0, to keep the
     task finishable in one sitting.

decisions_reserved:
  - "Which way the 4 `lower_is_better`/`direction` contradictions get resolved (flip the boolean, which
     touches the live MVP, or flip the direction, which contradicts the football reading). CPO decides
     when TASK 0 runs; the handover presents both, recommends neither as settled."
  - "Whether to widen `assert_no_uncatalogued_season_metric` beyond the two season models (issue #530) —
     referenced, deliberately NOT folded into TASK 0."

done_when:
  - TASK 0 in `.claude/active_work.md` specifies the values AND both gates, with their ordering and the
    reason each cannot pass earlier.
  - The 4 `lower_is_better`/`direction` contradictions are named explicitly, with the live-MVP consequence
    stated, so they are not discovered again from scratch.
  - The CPO's enforcement-over-intention rationale is recorded so the gates are not treated as optional.
  - No file outside `scope_paths` is touched (diff-verified); no test or seed is written in THIS task.
  - scope-auditor PASSes (the only routed reviewer; `contract.md` is on `artifact_only_never`, so this
    commit is not review-exempt).
  - CPO merges; I never merge.

amendments: (none)
