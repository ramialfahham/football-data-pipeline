# Review — fix/player-stats-complete-format

diff_sha256: 7d221422641db706d2ff26430672fc9656eec15625d890b9d8f059ae798300ba

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- All files in scope_paths; the impact map pastes the dbt ls lineage and gives measured row, match, key and cost figures.
- No coverage cut: the change widens refetching and adds a test; no metric, label, URL or frontend logic; the fetch pick stays in base.
- Thresholds declared with authority and date; no new mechanism; docs updated in the same branch; no secret or hardcoded competition.
- Round 2 delta: corrected cost figures (about 1.3 GB and 1 to 5 calls a night) replace the earlier ones everywhere; the data-contract qualifier matches the code.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The fetch choice sits in base and is per match: newest complete fetch, else newest, on (league_code, fixture_id); raw_ingested_at is not-null-tested, so the equality drops nothing silently.
- Grain unchanged: the existing uniqueness test still holds, and the dedup and collision guard now run inside one fetch.
- The cleaning's counted windows now see one fetch per match, the intended direction; existing base tests read the kept fetch.
- The new test fires only when the newest complete fetch has the stat for a player with minutes and the model has it for none; the cleaning cannot blank both for a whole match.
- Impact map: every direct reader of the changed models appears in the pasted lineage; the dropped rows and the second-id duplicates are disclosed.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- The refetch is due once: latest_fetch < kickoff + 14 days <= now; a failed batch retries next night; an idle competition is not switched to full mode.
- A payload without players is never the newer format; EXISTS and NOT EXISTS never yield null, so the ARRAY_AGG pick cannot fail.
- Round 1 FAIL closed in round 2: the coverage query runs twice a night, so about 1.3 GB; the API rate is measured over 12 nights per competition batch, 1 to 5 calls; data_contract.md carries the under-14-days qualifier.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The read_coverage test fails if the new branch is removed and its twin fails if the flag is ignored; FIXTURE_STATISTICS stays pinned.
- The row helper sets latest_in_newer_format explicitly, so no auto-created mock attribute can flip a test.
- The boundary tests pin <= on now and the strict < on the latest fetch; each guard has its own test.

## escalations
(none)
