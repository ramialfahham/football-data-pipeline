# Review — feature/166-future-match-page

diff_sha256: 69f7f4e379d7aeec570db924f8d73546f382a1f0a79ce0ecbb67de2a4d012d3a

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every path is in scope_paths; the block_standard.md Match page entry change carries a dated approved amendment.
- The impact map pastes the reader grep (one reader, [fixture].astro:33) and an empty dbt_project diff.
- No new strings, mechanism or reserved decision; the recurring cost is declared and measured.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every new select column exists in mart_competition_fixtures; _competition_fixture only casts and renames; the page's own fixture is still dropped.
- The tests pin the next-match row shape and the payload's is_next_round.
- A missing is_next_round renders as the next-match page, as the contract says.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every rendered field traces to the served match row; no new strings; compTBC is the match row's TBD text.
- The future page matches renders _31/_32: Head to head, then Next matches with the group head, a date heading per day and linked rows; no standing chip.
- The Match page entry expects only the parts both states show, so a future page sorting first cannot fail the check.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The export is read-only and pure; fixture_order is never null; the tests fail on a revert.
- The page set is unchanged; showStanding's one caller passes it; no new request kind, dependency or CI change.
- The design check's Expect narrowing matches its design and the recorded ruling.

## escalations
(none)
