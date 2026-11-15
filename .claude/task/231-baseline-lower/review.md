# Review — fix/baseline-lower-main-231 — 2026-11-15

diff_sha256: 62666a28ecf4c20b957229c387632dce0716cb8bcfe6583960d3d72d098c7224

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- The diff touches only baseline.json and contract.md, both in scope_paths; no amendments.
- Only removals and one lowered count; no pin rises; zero keys dropped as compare_rendered does.
- No page output, mechanism or recurring cost changes.

## platform-reviewer
VERDICT: PASS
risks_checked:
- JSON stays valid; missing keys read as 0 in compare_counts, so removing the entries is consistent.
- Nothing rises; the check stays fail-closed in both directions.
- The measured values are confirmed by the full-scope run in the CI image: 175 pages, 6 viewports, 0 failures.

## escalations
(none)
