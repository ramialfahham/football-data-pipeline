# Review — feature/145-sentence-generator

diff_sha256: 96b6a128a8e8f6e135f1dfb6b2d32e3eecc29f9f7dd947e842de05a9b5b5387a

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the generator is the new mechanism #145 specifies, declared with no recurring cost.
- No number is derived: every placeholder is a served count or team name; the DE and FI wording is recorded as approved with its date.
- The round-2 delta changes only tests/test_sentence.py and adds no wording or mechanism.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The counts come from mart_head_to_head's directed row looked up as (home, away), so wins are the home side's and losses the away side's; club and won follow that perspective in every branch.
- All four counts come from one recency window tested to sum to meetings_last5; every branch is reachable and fills every placeholder.
- A missing row, count or team name gives no intro; the round-2 cases pin each branch, including the away-leader path.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The wording choice matches design-mocks/gen_match_page.py h2h_sentence case by case, and the EN text matches the approved render.
- Every input is a served field; no zero or partial intro is fabricated; DE and FI keep the same placeholders.
- No markup, CSS or component changes; the build is byte-identical, so no rendered evidence is owed.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The generator is pure and re-run safe; the relative strings path resolves in the export job and in test:python.
- The strings.ts parser is identical to the copy gate's; a parser break fails the placeholder test.
- Round-1 finding resolved: each of the eleven wordings is asserted in EN, DE and FI, and each breakage named in round 1 now fails a case.
- Round 3: the lint rename of `l` to `lost` covers every use, `n in (w, lost)` is the same test, and the `{l}` placeholder key is unchanged.

## escalations
(none)
