# Task contract — ask the provider again for matches still missing player or team stats

objective: >
  Issue #298. The provider adds player and team stats to finished matches after the loader stops
  asking: on 15 Nov 2026, 5 of 20 sampled matches had data at the provider that no stored fetch
  carries. The nightly now asks again 7 and 30 days after kickoff for a match that still has no
  player stats or no team stats in any fetch. The one-off refetch script writes a provider answer
  only when it is no worse than every stored fetch in any section and better in at least one, so
  it can fill matches without line-ups. After merge it is run once on every such finished match.

refs: >
  #298 (measurement and provider check: comments on the issue, 15 Nov 2026). The re-fetch of current
  season and history, and the 7- and 30-day re-asks inside the existing nightly, approved in chat,
  15 Nov 2026, relayed by the coordinating session. Follows #309 (base takes a value from any
  stored fetch) and #176 (the refetch script).

scope_paths:
  - ingestion/api_football/coverage.py
  - ingestion/api_football/loads/batch_fixtures.py
  - scripts/refetch_from_provider.py
  - tests/test_coverage.py
  - tests/test_refetch_from_provider.py
  - tests/fixtures/apif/fixture_details_sample.json
  - docs/data_contract.md
  - docs/operations_guide.md
  - .claude/task/298-late-stats-refetch/contract.md
  - .claude/task/298-late-stats-refetch/review.md
  - .claude/task/298-late-stats-refetch/review_input.patch

impact_map: >
  writers: RAW_APIF_FIXTURE_DETAILS (append-only, one row per fetch) is written only by
  `batch_fixtures._insert_fixture_rows`, called by the nightly fanout
  (`run_batch_fixture_fanout_and_persist`) and by `scripts/refetch_from_provider.py fixtures`
  (grep -rn "_insert_fixture_rows" ingestion scripts). `coverage.read_coverage` reads it for the
  fanout plan (`orchestrator.py`), the idle/full mode decision (`ingest_plan.py` through
  `covered_for_league`, which skips a due player-stats fetch, so no competition changes mode) and
  the end-of-run completeness check (`completeness.py`).
  downstream: no model changes; new raw rows reach every reader of the source. Readers of
  source raw_apif_fixture_details (grep -rln raw_apif_fixture_details dbt_project/models):
  stg_apif__fixture_events, stg_apif__fixture_players, stg_apif__fixture_statistics,
  stg_apif__lineups. Their readers: base_apif__fixture_events, base_apif__fixture_players,
  base_apif__fixture_statistics, base_apif__lineup_sheets, base_apif__players, base_apif__teams.
  The dbt CLI and dbt MCP are blocked by the machine's application control in this session, so
  the downstream lineage below base is the `dbt ls --select base_apif__fixture_statistics+` and
  `base_apif__fixture_players+` output committed in .claude/task/309-every-fetch-values/contract.md
  (82 models: fct_fixture_team_stats, fct_fixture_player_stats, fct_fixture_lineup, dim_player,
  int_legs__team_match, int_legs__player_match and every int_player_* / int_team_* / mart_* model
  on them).
  layer_rules: check_layer_contract.py is unaffected (no model, no staging subdirectory); the raw
  table keeps its schema, partitioning and clustering.
  deploy_order: code only. The nightly change acts from the first nightly after merge. A mark is
  due only during the 7 days after it passes, so the nightly never sweeps old matches: on 15 Nov
  2026 the matches due under that rule need 4 requests in 3 competitions, against 28 requests for
  441 matches without the bound. Older matches reach raw only through the guarded backfill. The
  backfill runs after merge, by hand, outside 02:00–04:00 UTC (the script refuses that window),
  holding the ingest lock, and after a staging build that has read every raw row of the listed
  matches (the script refuses otherwise). Base and every model above pick the new rows up at the
  next nightly build.
  blast_radius: matches gain player rows, team stats, events or line-ups where the provider now has
  them and no stored fetch did. Measured on prod, 15 Nov 2026: 11,543 finished matches have no
  player stats or no team stats in any fetch (598 requests at 20 a request, per competition);
  1,433 of them are in the current season. Of 20 sampled matches, 5 gained a section. Every page
  and mart built on player or team match stats changes where a match gains them: match leaders,
  line-ups, rankings boards, team and player season figures, next-match form. The backfill script
  refuses an answer with fewer events, player rows, statistics lines or starters than a stored
  fetch, so it shortens nothing base holds. The nightly re-asks append without that check, as the
  existing 3-day second fetch and 14-day refetch do, and base resolves the fetches by the rules in
  data_contract.md "Both versions are kept deliberately": team stats, coach bio and blank player
  stats from any fetch (#309); a team's line-up and the event list from the newest fetch carrying
  them, so a shorter later list is followed as the provider's revision. Nightly cost: about 2
  extra requests a day, at most 7 (measured over the last 60 days, current seasons).

approved_design:
  - none: no page layout changes; values on existing pages change

decisions_taken: >
  The CPO decisions of 15 Nov 2026 (approved in chat, relayed by the coordinating session):
  a one-off re-fetch into raw of every finished match with no player stats or no team stats in any
  fetch, current season and history (about 600 requests), and nightly re-asks at 7 and 30 days
  after kickoff for a match still missing either, inside the existing nightly run, no extra run.

  RECURRING COST, declared: the 7- and 30-day re-asks add about 2 provider requests a day to the
  nightly (at most 7 a day over the last 60 days). Authority: the CPO decision above.
  NEW MECHANISM: none. The re-asks reuse the existing player-stats due flag that the 3-day second
  fetch and the 14-day newer-format refetch set. The backfill reuses scripts/refetch_from_provider.py.

  Engineering calls (no CPO class):
  - "Missing" means no fetch of the match has a player row, or no fetch has a team statistics line;
    the same test as the coverage query's existing `has_statistics`. The `has_players` expression
    is the one the measurement queries of 15 Nov 2026 ran on prod (11,543 matches).
  - A re-ask fires once per mark, when the latest fetch came before kickoff + 7 days (or + 30 days)
    and that mark passed less than 7 days ago, so a missed nightly heals within the week and a
    mark passed long ago is left to the backfill.
  - The parsing tests read tests/fixtures/apif/fixture_details_sample.json: three provider
    fixture-details payloads from the 15 Nov 2026 provider check (KL1 1507045 with every section,
    CAFCL 1619071 with statistics and a line-up block without startXI, FAC 1646794 with line-ups
    and statistics but no player rows), trimmed to 3 events, 2 player rows and 3 starters a team.
  - The refetch script's "two line-ups of eleven starters" condition is replaced by "no fewer
    starters for either team than a stored fetch". A match the provider has no line-ups for can
    then gain stats. Base takes a team's line-up from its newest fetch that has one, so an answer
    without line-ups never removes one.
  - The script writes an answer only when it is better than every stored fetch in at least one
    section (more events, player rows, statistics lines or starters for a team, or the complete
    player format). An answer equal to the stored data is not written, so raw does not grow by
    11,000 duplicate rows and no unrequested value revision enters base.
  - The backfill list is chosen at backfill time by one read-only query, quoted in the MR
    description and not kept in the repo: every match of base_apif__fixtures_next with status FT,
    AET or PEN, kickoff more than 3 days ago, no player row or no statistics line in any
    RAW_APIF_FIXTURE_DETAILS fetch, and a latest fetch more than 2 days old (the nightly has just
    asked for a newer one). On 15 Nov 2026 it lists 11,535 matches in 32 competitions; plan mode
    counts 598 requests.

decisions_reserved:
  - none: the CPO decided the re-fetch scope and the nightly cadence on 15 Nov 2026; what a page
    shows does not change, only which matches carry data.

done_when:
  - python -m pytest tests/test_coverage.py tests/test_refetch_from_provider.py tests/test_batch_fixtures.py -q passes
  - the validate-local fast gates pass
  - python scripts/refetch_from_provider.py fixtures --ids-file <the backfill list> (plan mode) prints the match and call counts, no call made
  - after merge: one --run with --max-calls 650; the request count used and the matches written are reported on #298

amendments:
  - 2026-11-15: + tests/fixtures/apif/fixture_details_sample.json — authority: the standing
    sample-based-tests rule the data-engineer reviewer applies to response parsing; content: the
    trimmed provider sample above. The nightly mark is bounded to 7 days and the nightly path's
    blast radius is restated, both from round-1 review findings.
