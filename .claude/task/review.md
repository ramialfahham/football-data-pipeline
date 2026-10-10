# Review — fix/standings-vl-split-groups

diff_sha256: 10f307bb990e52447893cb5a17cf7958561f89858c82e833f6dc35acbd0459b2

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; the seed row matches the text the contract records as approved in chat, 2026-10-10; no reserved decision is touched.
- §10 classes: no new mechanism, metric definition, URL, shipped number or cost change; the threshold declarations match the diff.
- The impact_map is present and evidenced; layering.md names no row count or section names, so it needs no update.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Priority 15 is tried before the group pattern (20) in both mart_standings.sql and the test, which take the lowest matching priority; `relegr?ation` covers both spellings.
- The seed's not_null, unique and accepted_values tests hold for the new row; none is weakened.
- With both VL 2026 halves as split_round, the season has no group section, so the test's league-next-to-groups clause cannot fire; the frontend branches only on ranking, so no page changes.

## escalations
(none)
