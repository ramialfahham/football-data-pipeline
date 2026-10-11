# Review — fix/extra-time-final-score

diff_sha256: 8e2d7c04f9ecc65a1b33926edc4385dfbbd967b64f3cc482318c7e6ed126f9e6

rounds: 4

rounds_cap_override: the approach was reworked from a rule into seed corrections and reviewed afresh; a fourth round approved in chat, 2026-10-11.

## scope-auditor
VERDICT: PASS
risks_checked:
- Against main the diff is the contract, 26 seed rows and the detector test, all in scope_paths; every file of the withdrawn rule is back at main's version; the rework is recorded as an amendment with its approval.
- The seed is the existing mechanism (source_kind match_reports with two sites is already accepted by its schema and test); no new mechanism, cost, column or label; the award kind (#176) and the shoot-out score (#178) are untouched.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- base_apif__fixtures_next applies each row through coalesce and keeps the provider's score beside it; awarded is false on every row, so the status stays AET/PEN; the score reaches fct_fixture, the stats models and their cleaning tests through the one model, so they cannot drift apart.
- The 26 fixture ids are unique and new; each row carries two https URLs on different sites; the detector counts only open-play goals and own goals after minute 90 as evidence, so the 15 unlabelled shoot-outs are not flagged, and its comment states the one case it cannot catch.

## escalations
- question: Review rounds are capped at three; allow a fourth for the reworked MR?
  CPO ANSWER: allowed; approved in chat, 2026-10-11.
