# Review — claude/298-player-data-proof-5518cd — 2026-11-15

diff_sha256: f8d2ab16a7d487c277d673255c257d330cf521c0384b63bc69c10c64a1785905

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the one amendment (the provider sample file) has a date and an authority line, and a test fixture is not a §10 class.
- No product, metric, label or URL change; decisions_reserved names the CPO decision of 15 Nov 2026.
- No new mechanism: late_fetch_due feeds the existing player-stats due flag; the backfill reuses scripts/refetch_from_provider.py.
- Recurring cost is declared (about 2 requests a day, at most 7) with its authority; the 7-day window only narrows what the nightly fetches, and the first-night count (4 requests) is stated.
- Impact map present; lineage below base cites the dbt ls output committed with #309, as the dbt CLI is blocked here; not a coverage cut.
- The refetch guard now writes more matches, not fewer; the "adds nothing" refusal prevents duplicate rows.
- data_contract.md and operations_guide.md move with the code; sentences are definitional; no page surface is touched.
- Round 2 delta: the restated blast_radius no longer overclaims; the sample file holds public provider data only.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Writes stay WRITE_APPEND; each mark fires once; completeness keeps a due fixture visible until fetched; raw schema unchanged.
- Stored starters read from stg_apif__lineups (team_id, start_xi_json exist); STAGING_TABLES guard includes it.
- Round 2, finding 1 resolved: tests/fixtures/apif/fixture_details_sample.json holds three real-shape payloads (every section; statistics with a line-up block without startXI; line-ups and statistics without players); TestProviderSample counts traced by hand; _lineup() carries a team id. The has_players SQL is not run offline; it is the expression the prod measurement ran, accepted.
- Round 2, finding 2 resolved: late_fetch_due is bounded to 7 days after each mark, so the nightly cannot sweep history; older gaps reach raw only through the guarded script; tests pin the window edge and a 400-day-old match.
- blast_radius states that nightly re-asks append without the script's check, as the 3-day and 14-day fetches do, matching data_contract.md.
- Completeness: a fixture past its window reads covered for player stats as before; no new permanent gap.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 finding fixed: the 7-day LATE_FETCH_WINDOW stops the first nightly sweeping old matches unguarded; boundaries read from code (days 7–14 and 30–37), a fetch inside a window moves latest_fetch past the mark.
- Tests fail if the bound is reverted (400-day match, window edge to the minute); the read_coverage late-fetch tests fall inside the window.
- Contract deploy_order and blast_radius match the code and no longer overclaim.
- The sample fixture's counts recomputed by hand against payload_counts, _gains and refusal_reasons; no credentials or private data.
- Round 1 items unchanged by the delta: script run safety (lock, window, cap, deadline), stored-count SQL, re-run writes nothing.

## escalations
(none)
