# Review — feat/235-table-exact — 2026-10-29

diff_sha256: 7a7f6b3d0e4658fecb6cc55d59f23c117876332f2e4b353f90a4beb07a06bbe5

rounds: 4

rounds_cap_override: the first MR data build failed the published-table test on places; the fourth round reviews the fixes, approved in chat, 2026-10-29

## scope-auditor
VERDICT: PASS
risks_checked:
- Every path in the delta is in scope_paths; the corrections, the Portugal condition and the test change are recorded in the amendments, the Saudi order with its approval.
- The five correction rows use the existing official-correction mechanism; the Portugal condition is an existing accepted value and a reading of the taken-as-published rule.
- The test changes narrow the comparison only where a correct table would fail; it stays an error.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- A correction applies on a table with its played count or on every past-season table; corrections are unique per row, so no fan-out, and the trailing-space group matches through base, the corrections test and the raw group.
- The test's rule version is the model's latest version per league, season and phase; the previous-place flag covers only teams level on points, goal difference and goals in SPL 2026 in season.
- The Portugal in-season head-to-head points now wait for both games, like the goal-difference row beside it.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The test is an error with stored failures, and nothing downgrades it.
- The exemption needs a previous_position rule row, so it cannot spread to another league; points are still compared.
- Both seeds keep CRLF and parse; the raw snapshot scan is about 203 MB a run and grows daily, measured before the merge.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- The corrected rows add up: played, points and goal difference; Verona above Spezia by the play-off, Toulouse above Lorient on goal difference.
- Portugal's in-season head-to-head counts once the level teams have met twice, as the league's table shows after matchday 9.
- Saudi in-season order by last season's place follows points, goal difference and goals; points stay compared for those teams.

## escalations
(none)
