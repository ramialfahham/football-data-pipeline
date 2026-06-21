# Review — fix/event-team-id-recovery — 2026-06-21

> Complete deep-backfill DQ fix (bounded defect set, enumerated via a clean build): events team_id
> recovery (base) + self-heal (fct_fixture_event) + mis-placed standings not_null test removed
> (stg_apif__generic.yml, CPO-approved) + player id-collision drop (base_apif__fixture_players) with the
> already-committed rows healed by a one-time CPO-authorized full-refresh of fct_fixture_player_stats
> (Option B). Routing: dbt -> analytics-engineer; scope-auditor always. BOTH PASS. No FAIL.

diff_sha256: 1ac415d54cf0a9fdb7dc1832854d13e5d1087f66bc7c7d3b63b9b90d716ad5d9

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Full-refresh is the correct DELETE-type heal: fct_fixture_player_stats uses unique_key merge
  (insert/update, never delete), so the 4 committed collision rows can't be removed by any incremental
  run — the one-time --full-refresh from the collision-dropped base view is structurally the only fix
  (the events self-heal is an UPDATE, inapplicable to a deletion). Executed; verified 0 remaining
  collisions. All consumers (int_legs__player_match, mart_player_match_log, mart_fixture_stats__player)
  are materialized tables, full-rebuilt from the clean fct → grain tests pass; no incremental
  intermediate retains stale rows. The base qualify guard is permanent (prevents recurrence).
- Events recovery + self-heal + standings test removal unchanged from prior PASS: recovery runs over
  the deduped set (no stale-null poisoning); self-heal merge-updates committed null team_sk in place,
  self-limiting; standings cleanliness preserved at the cleaned layer (base drop + fct_standings.team_sk
  not_null + relationships). base_players collision-drop is surgical (min(team_id)=max(team_id) over
  (fixture, player); 2 pairs / 4 rows, no false positives).

## scope-auditor
VERDICT: PASS
risks_checked:
- Heal verified pre-merge by the gating CI (resolves the prior ESCALATE): the full-refresh's success is
  not taken on trust — #527's ci-data-build rebuilds int_legs__player_match + mart_player_match_log
  (materialized tables) from the live fct and runs their (fixture,player) grain tests; if the heal had
  failed they'd be red, and the CPO merges only a green PR. So there is no false-green / merge-unverified
  window. The one-time --full-refresh is recorded as a CPO-authorized ("Execute B") one-time deploy, not
  a routine-local-build precedent.
- Scope + faithfulness: the diff touches only scope_paths (int_legs/mart are NOT changed — B used the
  full-refresh, not consumer edits); all 5 amendments carry CPO authority; the fix is "fix the defects,
  keep all deep history" (no depth-cut / avoid); reserved items (#526 38-row integrity, finding-1) stay
  reserved. No Appendix A anti-pattern.

## escalations
- question: Removing the not_null test on stg_apif__standings.team_id (mis-placed on faithful staging,
  which the provider leaves null in old data) — is that a §10 DQ decision the CPO must bless?
  CPO ANSWER: Approved (2026-06-21): "The fix: remove that staging-layer test." DQ preserved at the
  cleaned layer (base_apif__standings drops null team_id; fct_standings.team_sk has not_null +
  relationships(dim_team)).
- note: the scope-auditor's round-N question on verifying the one-time full-refresh was resolved by the
  §11 premise check (the gating ci-data-build grain tests verify the heal pre-merge) — re-reviewed to
  PASS, no CPO ruling required.
