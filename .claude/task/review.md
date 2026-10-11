# Review — feat/goal-definition

diff_sha256: 420187eea4a46fe2363cb515d23c619c41955a7377b0d8f390df69b55e8d2153

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file in the diff is in scope_paths; the goal definition, the nameless-event rule, negative minutes as shoot-out kicks and the award columns match decisions_taken; nothing reserved (the goals list, the state, the corrections seed, the page) is touched.
- Doc-sync: layering.md, core.yml, the fct_fixture_event header and cleaning_rules.md no longer say the assist has no id, and cleaning_rules.md carries both new goal-event rules.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The definition lives once in base_apif__fixture_events; staging only casts the assist id, core only passes the flags through; the new score join adds no cycle and no fan-out (one row per fixture), and no other model or test keeps its own goal or shoot-out filter.
- The new columns carry not_null, relationships and accepted_values tests; the four goal tests are repointed to is_goal, not removed; the impact map's 68-model lineage and the measured blast radius match the change.

## escalations
(none)
