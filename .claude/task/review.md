# Review — chore/176-retire-team-fixture-stats

diff_sha256: 4d3f64fce1c12f777d43ec21179fbdefb64d020032abfdae63ae8f7d5b43f1df

rounds: 1

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- No reader of the deleted mart is left outside the three items the contract reserves.
- The new has_team_stats join reads mart_team_window_metrics' match rows, unique on (fixture_sk, team_sk), so the form list cannot fan out and the flag stays non-null.
- The flag now means shots present on the match window; it can differ from the provider's any-stat line, as the contract declares, counted before merge.
- The formula test's Jinja still renders valid SQL: the comma and union all are conditional on the last surface.
- The pass-accuracy check on match rows stays covered by the window mart's surface; no metric was created or redefined.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- No component, page or spec reads matchstats or has_team_stats; types.ts only declares the flag.
- A changed flag value cannot change a rendered page; no new field or sample key.
- The wireframe edit removes only the dead data-source row; the core-document edits match the approved texts.

## platform-reviewer
VERDICT: PASS
risks_checked:
- No CI job, deploy script, nightly entrypoint, manifest or test still names the matchstats entity.
- The metric map loses exactly the 7 rows of the deleted model; the repointed fan question has its map row and accepted window value.
- The code-history pin moves by exactly the two flagged lines in the one deleted file.
- Deploy order: the stale prod table is read by nothing; old and new images are compatible either way.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope; the mechanical removals follow from the objective.
- The four document edits match the approved texts character for character; the has_team_stats source and the fan question match decisions_taken.
- The reserved items are untouched: the prod table drops, the player wireframe, GAP-07, the design mocks.
- Threshold declarations honest: a removal, the cost falls, measured before merge.

## escalations
(none)
