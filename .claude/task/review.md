# Review — fix/fixture-title-unique — #155

diff_sha256: 4a91200660c42990c2b0628435409b1c8d788004fb8e15fc993355859568ed2f

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: every changed file is in scope_paths; the wording is the CPO's chat decision recorded in decisions_taken and shown on the MR head; no protected path; the impact_map carries the grep of seoFixtureTitle's single consumer and the measured duplicate and width counts; 01_fixture_page.md §8 updated in the same diff; formatShortDate and the served kickoff reused, no new mechanism or cost; no credential-shaped string; canonical, JSON-LD name, breadcrumb and description unchanged.
- Round 2 delta: only the EN comment above seoFixtureTitle changed, now matching the 535px figure verified in round 1; no string, scope or contract change.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1: `date` binds to the payload's served kickoff (shape_fixture_payload), already used for the JSON-LD startDate; the three strings match the CPO's chosen wording; §8's rule that the competition stays out of the title is kept; formatShortDate falls back to the dash on a null kickoff; the full-scale audit (14,905 pages, 0 violations) and the mutation (date removed, 11 duplicate EN titles) demonstrate the fix; §8 no longer mentions Preview. Noted a stale source comment in strings.ts.
- Round 2 delta: the stale comment now describes the date and the 535px measurement; no string value changed.

## escalations
- question: Which match-page title fixes #155, "Date replaces Preview" or "Date after Preview" (each breaks one recorded rule)?
  CPO ANSWER: Date replaces Preview (answered in chat; recorded in contract.md decisions_taken).
