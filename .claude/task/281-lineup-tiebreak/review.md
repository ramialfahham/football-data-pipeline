# Review — claude/281-lineup-tiebreak-34cf30 — 2026-11-15

diff_sha256: 450702a6bdc2f836bf7e89e0217755db3a3b7fe9c41019b7524a68a630511442

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- The three changed paths are inside scope_paths, and the contract has no amendments.
- The only behaviour change is row_number to rank in the latest-fetch pick. Zero ties are measured on today's data, so no shipped number changes. The player-row rule in cleaning_rules.md is unchanged.
- The recurring cost of the new test (about 0.11 GB per build) is declared in decisions_taken. A singular test is an existing mechanism.
- The impact map pastes the lineage and the measured blast radius. No secrets, workflows or frontend files are in the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the fetch dedup stays in base_apif__lineup_sheets and reads only stg_apif__lineups.
- With rank, two fetches tied on ingest time both survive `latest`. Their rows collide on the sheet grain, so the existing grain test fails. Where they do not collide, the new singular test fails instead.
- provider_players in base_apif__lineups orders by is_starter desc, sheet_index asc. That is the first-listing rule in cleaning_rules.md, and the sheet grain test covers its key.
- The new test groups by the raw team id while the model groups by the corrected one. Any tie in the latest pick still fails the grain test, and no concrete case of a lender tie under a corrected id exists. Not a defect.
- No metric, seed, project config, consumption file or league identifier in the diff.

## escalations
(none)
