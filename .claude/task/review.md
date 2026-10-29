# Review — feat/235-table-exact — 2026-10-29

diff_sha256: 943fa3acacad44799fe8ce3aea15e06e5cbc6ab0793ed659e24b0d82400396b3

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; refs cite the approved plan, the points_rank texts and the temporary result.
- The computed-position sentence is removed from the metric rules; the table is rebuilt to equal the published one and tested as an error.
- No new export, frontend change, dependency or run cadence; the round-1 fixes stay inside the approved plan.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The model is unique on league, season, section, kick-off and team; the previous season's place reads single-table seasons only, so it cannot fan out.
- Deduction steps count from their effective date; the published-table test leaves out a snapshot with a step after the matched kick-off's day and fails a league-season with no comparable snapshot.
- The second head-to-head pass groups by the first pass's conditioned values; a phase with no rules orders by points alone and level teams get no place.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The seeds carry closed-list and uniqueness tests; every rule version ends in one undecidable row, tested.
- The replaced warning tests are removed; the new table tests are errors with stored failures.
- The raw snapshot scan in the published-table test is measured on the MR build before the merge.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Each league's order follows its official regulation per season and phase; a tie the results cannot settle gives no place.
- The temporary 3-0 counts for both teams only between its dates; the replayed match kicked off on 7 April 2021, outside them.
- The points_rank description and interpretation agree; table points are the published standings value, points_won stays points from results.

## escalations
(none)
